// SKG core (C++11). Dipakai sketch ESP32 (bob_esp32.ino) dan host test (g++).
// Hasil SHA-1 identik dgn Python hashlib.sha1 -> kunci ESP32 == kunci Alice (Python).
// CATATAN: SHA-1 deprecated/rawan kolusi. Dipakai untuk tujuan ajar, bukan keamanan produksi.
#ifndef SKG_H
#define SKG_H
#include <stdint.h>
#include <math.h>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <algorithm>
#include <functional>

namespace skg {

// ---------------- SHA-1 ----------------
inline uint32_t _rotl32(uint32_t x, int n){ return (x << n) | (x >> (32 - n)); }

inline std::string sha1_hex(const std::string& data){
  uint32_t h0=0x67452301, h1=0xEFCDAB89, h2=0x98BADCFE, h3=0x10325476, h4=0xC3D2E1F0;
  std::vector<uint8_t> msg(data.begin(), data.end());
  uint64_t ml = (uint64_t)data.size() * 8;
  msg.push_back(0x80);
  while(msg.size() % 64 != 56) msg.push_back(0x00);
  for(int i=7;i>=0;i--) msg.push_back((uint8_t)(ml >> (8*i)));
  for(size_t off=0; off<msg.size(); off+=64){
    uint32_t w[80];
    for(int i=0;i<16;i++)
      w[i] = ((uint32_t)msg[off+i*4]<<24)|((uint32_t)msg[off+i*4+1]<<16)
           | ((uint32_t)msg[off+i*4+2]<<8)|((uint32_t)msg[off+i*4+3]);
    for(int i=16;i<80;i++) w[i]=_rotl32(w[i-3]^w[i-8]^w[i-14]^w[i-16],1);
    uint32_t a=h0,b=h1,c=h2,d=h3,e=h4;
    for(int i=0;i<80;i++){
      uint32_t f,k;
      if(i<20){ f=(b&c)|((~b)&d); k=0x5A827999; }
      else if(i<40){ f=b^c^d; k=0x6ED9EBA1; }
      else if(i<60){ f=(b&c)|(b&d)|(c&d); k=0x8F1BBCDC; }
      else { f=b^c^d; k=0xCA62C1D6; }
      uint32_t tmp=_rotl32(a,5)+f+e+k+w[i];
      e=d; d=c; c=_rotl32(b,30); b=a; a=tmp;
    }
    h0+=a; h1+=b; h2+=c; h3+=d; h4+=e;
  }
  uint32_t hs[5]={h0,h1,h2,h3,h4};
  static const char* hx="0123456789abcdef";
  std::string s; s.reserve(40);
  for(int j=0;j<5;j++) for(int i=7;i>=0;i--) s.push_back(hx[(hs[j]>>(4*i))&0xF]);
  return s;
}

// ---------------- 1. QUANTISASI guard-band ----------------
inline void _mean_std(const std::vector<double>& v, double& m, double& s){
  double sum=0; for(size_t i=0;i<v.size();i++) sum+=v[i]; m=sum/v.size();
  double var=0; for(size_t i=0;i<v.size();i++){ double d=v[i]-m; var+=d*d; } var/=v.size(); s=sqrt(var);
}

// kept[index]=bit (0/1). Sampel di pita [lo,up] dibuang (ambigu).
inline std::map<int,int> quantize_guardband(const std::vector<double>& v, double alpha){
  double m,s; _mean_std(v,m,s);
  double up=m+alpha*s, lo=m-alpha*s;
  std::map<int,int> kept;
  for(int i=0;i<(int)v.size();i++){
    if(v[i]>=up) kept[i]=1;
    else if(v[i]<=lo) kept[i]=0;
  }
  return kept;
}

// ---------------- 2. SIFTING ----------------
inline std::vector<int> common_positions(const std::map<int,int>& self, const std::vector<int>& peer){
  std::set<int> ps(peer.begin(), peer.end());
  std::vector<int> out;                       // std::map sudah terurut naik
  for(std::map<int,int>::const_iterator it=self.begin(); it!=self.end(); ++it)
    if(ps.count(it->first)) out.push_back(it->first);
  return out;
}
inline std::vector<int> bits_at(const std::map<int,int>& kept, const std::vector<int>& pos){
  std::vector<int> b; for(size_t i=0;i<pos.size();i++) b.push_back(kept.find(pos[i])->second); return b;
}

// ---------------- 3. REKONSILIASI (Cascade) ----------------
struct PCG32 {
  uint64_t state, inc;
  PCG32(uint64_t seed, uint64_t seq=54){ state=0; inc=(seq<<1)|1; step(); state+=seed; step(); }
  void step(){ state = state*6364136223846793005ULL + inc; }
  uint32_t next(){ uint64_t old=state; step(); uint32_t xs=(uint32_t)(((old>>18)^old)>>27); uint32_t rot=(uint32_t)(old>>59); return (xs>>rot)|(xs<<((-rot)&31)); }
};

inline std::vector<int> _shuffle(int n, uint64_t seed){
  PCG32 rng(seed);
  std::vector<uint32_t> keys(n);
  for(int i=0;i<n;i++) keys[i]=rng.next();
  std::vector<int> idx(n); for(int i=0;i<n;i++) idx[i]=i;
  std::sort(idx.begin(), idx.end(), [&](int a,int b){ return keys[a]!=keys[b] ? keys[a]<keys[b] : a<b; });
  return idx;
}

inline int block_parity(const std::vector<int>& bits, const std::vector<int>& idxs){
  int p=0; for(size_t i=0;i<idxs.size();i++) p^=bits[idxs[i]]; return p;
}

// oracle(indices) -> parity Alice (lewat jaringan). Mengubah bits_b agar identik Alice.
inline int cascade_correct(std::vector<int>& bits_b, std::function<int(const std::vector<int>&)> oracle,
                           int n, int passes=14, int k0=4){
  int queries=0; int k=k0;
  for(int p=0;p<passes;p++){
    std::vector<int> perm=_shuffle(n, 1000+p);
    for(int start=0; start<n; start+=k){
      int end = (start+k<n)?(start+k):n;
      std::vector<int> block(perm.begin()+start, perm.begin()+end);
      int pa=oracle(block); queries++;
      if(pa==block_parity(bits_b,block)) continue;
      std::vector<int> lo=block;
      while(lo.size()>1){
        int half=lo.size()/2;
        std::vector<int> left(lo.begin(), lo.begin()+half);
        int pal=oracle(left); queries++;
        if(pal!=block_parity(bits_b,left)) lo=left;
        else lo=std::vector<int>(lo.begin()+half, lo.end());
      }
      bits_b[lo[0]]^=1;
    }
    k = (k*2<n)?(k*2):n;
  }
  return queries;
}

// ---------------- 4. KUNCI ----------------
inline std::string derive_key(const std::vector<int>& bits){
  std::string s; s.reserve(bits.size());
  for(size_t i=0;i<bits.size();i++) s.push_back(bits[i]?'1':'0');
  return sha1_hex(s);
}

} // namespace skg
#endif
