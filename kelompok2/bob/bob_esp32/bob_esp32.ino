/*
 * BOB (ESP32) — Secret-Key-Generation sederhana, sisi corrector + TCP server.
 * Pasangan: alice/alice.py di laptop (Alice = client + reference).
 * Toolchain: Arduino IDE / arduino-cli, board "ESP32 Dev Module".
 *
 * Alur (sama dgn Python):
 *   1. Quantisasi guard-band RSSI -> bit
 *   2. Sifting: tukar indeks, ambil irisan posisi
 *   3. Rekonsiliasi Cascade: koreksi bit agar identik Alice
 *   4. Privacy amplification: kunci = SHA-1(bit)
 *   5. Verifikasi H(H(kunci)) -> MATCH/RETRY
 */
#include <WiFi.h>
#include "skg.h"
#include "synced_bob.h"

// ====== ISI BAGIAN INI ======
const char* WIFI_SSID = "GANTI_SSID";
const char* WIFI_PASS = "GANTI_PASSWORD";
const int   PORT      = 6000;
const double ALPHA    = 1.0;   // HARUS sama dgn alice.py
// =============================

WiFiServer server(PORT);

// ---- helper line-based di atas WiFiClient ----
void sendline(WiFiClient& c, const std::string& s){
  c.print(s.c_str());
  c.print('\n');
}
String recvline(WiFiClient& c, unsigned long timeout_ms=20000){
  String line; unsigned long t0=millis();
  while(millis()-t0 < timeout_ms){
    while(c.available()){
      char ch=c.read();
      if(ch=='\n') return line;
      if(ch!='\r') line+=ch;
      t0=millis();
    }
    if(!c.connected() && !c.available()) break;
    delay(1);
  }
  return line;
}

std::string join_ints(const std::vector<int>& v){
  std::string s;
  for(size_t i=0;i<v.size();i++){ if(i) s+=','; s+=std::to_string(v[i]); }
  return s;
}
std::vector<int> split_ints(const String& s){
  std::vector<int> out; int val=0; bool any=false, neg=false;
  for(size_t i=0;i<s.length();i++){
    char ch=s[i];
    if(ch=='-'){ neg=true; any=true; }
    else if(ch>='0'&&ch<='9'){ val=val*10+(ch-'0'); any=true; }
    else if(ch==','){ if(any) out.push_back(neg?-val:val); val=0; any=false; neg=false; }
  }
  if(any) out.push_back(neg?-val:val);
  return out;
}

void runSKG(WiFiClient client){
  // 1. quantisasi
  std::vector<double> rssi; rssi.reserve(N_BOB);
  for(int i=0;i<N_BOB;i++) rssi.push_back((double)RSSI_BOB[i]);
  std::map<int,int> kept = skg::quantize_guardband(rssi, ALPHA);
  Serial.printf("Bob: N=%d kept(quantisasi)=%d\n", N_BOB, (int)kept.size());

  // 2. sifting: kirim indeks Bob, terima posisi bersama
  std::vector<int> keys;
  for(std::map<int,int>::iterator it=kept.begin(); it!=kept.end(); ++it) keys.push_back(it->first);
  sendline(client, join_ints(keys));
  std::vector<int> pos = split_ints(recvline(client));
  std::vector<int> bits_b = skg::bits_at(kept, pos);
  int n = pos.size();
  Serial.printf("Sifting: posisi bersama = %d\n", n);

  // 3. rekonsiliasi: oracle tanya parity Alice via jaringan
  std::function<int(const std::vector<int>&)> oracle =
    [&](const std::vector<int>& idxs)->int{
      sendline(client, join_ints(idxs));
      String r = recvline(client);
      return r.toInt();
    };
  int q = skg::cascade_correct(bits_b, oracle, n);
  sendline(client, "DONE");
  Serial.printf("Rekonsiliasi selesai, query parity = %d\n", q);

  // 4. kunci + verifikasi
  std::string key = skg::derive_key(bits_b);
  String hh_alice = recvline(client);
  std::string status = (skg::sha1_hex(key) == std::string(hh_alice.c_str())) ? "MATCH" : "RETRY";
  sendline(client, status);

  // (MODE DEMO) kirim kunci Bob agar Alice bisa menampilkan & membandingkan langsung.
  // PERINGATAN: SKG asli TIDAK PERNAH mengirim kunci (Eve bisa menyadap). Hanya untuk demo.
  sendline(client, key);

  Serial.printf("STATUS: %s\n", status.c_str());
  Serial.printf("Kunci Bob: %s\n", key.c_str());
}

void setup(){
  Serial.begin(115200);
  delay(500);
  Serial.printf("\nWiFi connect %s ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while(WiFi.status()!=WL_CONNECTED){ delay(400); Serial.print("."); }
  Serial.println();
  Serial.print("WiFi OK, IP ESP32 = ");
  Serial.println(WiFi.localIP());     // <- catat IP ini, isikan ke alice.py (BOB_IP)
  server.begin();
  Serial.printf("Bob menunggu Alice connect di port %d...\n", PORT);
}

void loop(){
  WiFiClient client = server.available();
  if(client){
    Serial.println("Alice terhubung.");
    runSKG(client);
    client.stop();
    Serial.println("Selesai. Reset ESP32 untuk ulang.\n");
  }
  delay(10);
}
