// SKG core (C++11). Dipakai sketch ESP32 (bob_esp32.ino) dan host test (g++).
// Hasil SHA3-256 identik dgn Python hashlib -> kunci ESP32 == kunci Alice (Python).
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

// ---------------- SHA3-256 (Keccak) ----------------
static const uint64_t _RC[24] = {
  0x0000000000000001ULL,0x0000000000008082ULL,0x800000000000808AULL,
  0x8000000080008000ULL,0x000000000000808BULL,0x0000000080000001ULL,
  0x8000000080008081ULL,0x8000000000008009ULL,0x000000000000008AULL,
  0x0000000000000088ULL,0x0000000080008009ULL,0x000000008000000AULL,
  0x000000008000808BULL,0x800000000000008BULL,0x8000000000008089ULL,
  0x8000000000008003ULL,0x8000000000008002ULL,0x8000000000000080ULL,
  0x000000000000800AULL,0x800000008000000AULL,0x8000000080008081ULL,
  0x8000000000008080ULL,0x0000000080000001ULL,0x8000000080008008ULL };
static const int _ROTC[24] = {1,3,6,10,15,21,28,36,45,55,2,14,27,41,56,8,25,43,62,18,39,61,20,44};
static const int _PILN[24] = {10,7,11,17,18,3,5,16,8,21,24,4,15,23,19,13,12,2,20,14,22,9,6,1};

inline uint64_t _rotl(uint64_t x, int n){ return (x << n) | (x >> (64 - n)); }

inline void _keccak_f(uint64_t st[25]){
  for(int r=0;r<24;r++){
    uint64_t bc[5];
    for(int i=0;i<5;i++) bc[i]=st[i]^st[i+5]^st[i+10]^st[i+15]^st[i+20];
    for(int i=0;i<5;i++){
      uint64_t t=bc[(i+4)%5]^_rotl(bc[(i+1)%5],1);
      for(int j=0;j<25;j+=5) st[j+i]^=t;
    }
    uint64_t t=st[1];
    for(int i=0;i<24;i++){ int j=_PILN[i]; uint64_t tmp=st[j]; st[j]=_rotl(t,_ROTC[i]); t=tmp; }
    for(int j=0;j<25;j+=5){
      uint64_t row[5];
      for(int i=0;i<5;i++) row[i]=st[j+i];
      for(int i=0;i<5;i++) st[j+i]=row[i]^((~row[(i+1)%5])&row[(i+2)%5]);
    }
    st[0]^=_RC[r];
  }
}

inline std::vector<uint8_t> sha3_256(const std::string& data){
  const int RATE=136;
  std::vector<uint8_t> msg(data.begin(), data.end());
  msg.push_back(0x06);
  while(msg.size()%RATE!=0) msg.push_back(0x00);
  msg.back()^=0x80;
  uint64_t st[25]; for(int i=0;i<25;i++) st[i]=0;
  for(size_t off=0; off<msg.size(); off+=RATE){
    for(int i=0;i<RATE/8;i++){
      uint64_t lane=0;
      for(int b=0;b<8;b++) lane |= (uint64_t)msg[off+i*8+b] << (8*b);
      st[i]^=lane;
    }
    _keccak_f(st);
  }
  std::vector<uint8_t> out;
  while(out.size()<32){
    for(int i=0;i<RATE/8 && out.size()<32;i++)
      for(int b=0;b<8 && out.size()<32;b++) out.push_back((uint8_t)(st[i]>>(8*b)));
    if(out.size()<32) _keccak_f(st);
  }
  out.resize(32);
  return out;
}

inline std::string sha3_256_hex(const std::string& data){
  std::vector<uint8_t> d=sha3_256(data);
  static const char* hx="0123456789abcdef";
  std::string s; s.reserve(64);
  for(size_t i=0;i<d.size();i++){ s.push_back(hx[d[i]>>4]); s.push_back(hx[d[i]&15]); }
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
  return sha3_256_hex(s);
}

} // namespace skg
#endif
