// Simulated adapters only. Production functions are inserted by test_exporter_guards.py.
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
using string = std::string;
using datetime = long;
using ulong = unsigned long;
constexpr int INVALID_HANDLE=-1;
constexpr int FILE_READ=1, FILE_WRITE=2, FILE_BIN=4, TERMINAL_CONNECTED=1;
constexpr int INSTRUMENT_COUNT=5, TIMEFRAME_COUNT=3;
long VerifiedSequenceFloor=-1;
int ExpectedBrokerUtcOffsetSeconds=10800, SequenceGuardHandle=-1;
unsigned long Sequence=0, ClockStableSince=0;
string SequenceStorageKey, ClockPauseReason;
bool SequenceFault=false, ClockObserved=false;
datetime FirstObservedBrokerTime=0, PublishedCheckpoint[5][3];
bool exists=false, variable=true, locked=false, fail_write=false, connected=true;
double gv=477;
std::vector<double> disk;
size_t position=0;
long utc_clock=100000, broker_clock=110800, quote_clock=110800;
unsigned long ticks=1;
int error_code=0;
bool MathIsValidNumber(double x) { return std::isfinite(x); }
double MathFloor(double x) { return std::floor(x); }
double MathMax(double a,double b) { return std::fmax(a,b); }
string BuildSequenceStorageKey() { return "test-source-key"; }
bool FileIsExist(const string&) { return exists; }
int FileOpen(const string&,int flags) { assert(flags==(FILE_READ|FILE_WRITE|FILE_BIN)); if(locked) return -1; locked=true; exists=true; position=0; return 1; }
size_t FileSize(int) { return disk.size()*8; }
bool FileSeek(int,long,int) { position=0; return true; }
int FileWriteDouble(int,double v) { if(fail_write) return 0; if(position>=disk.size()) disk.push_back(v); else disk[position]=v; ++position; return 8; }
double FileReadDouble(int) { return disk.at(position++); }
void FileFlush(int) {}
void ResetLastError() { error_code=0; }
int GetLastError() { return error_code; }
bool GlobalVariableCheck(const string&) { return variable; }
double GlobalVariableGet(const string&) { return gv; }
long GlobalVariableSet(const string&,double v) { variable=true; gv=v; return 1; }
void GlobalVariablesFlush() {}
void Print(const string&) {}
long TimeTradeServer() { return broker_clock; }
long TimeGMT() { return utc_clock; }
long TimeCurrent() { return quote_clock; }
long TerminalInfoInteger(int) { return connected; }
unsigned long GetTickCount64() { return ticks; }
// EXPORTER_GUARD_FUNCTIONS
void reset() {
    VerifiedSequenceFloor=-1; SequenceGuardHandle=-1; Sequence=0; SequenceFault=false;
    ClockObserved=false; ClockStableSince=0; FirstObservedBrokerTime=0;
    exists=false; variable=true; locked=false; fail_write=false; gv=477; disk.clear();
    position=0; connected=true; ticks=1; utc_clock=100000; broker_clock=110800; quote_clock=110800;
    for(auto &row:PublishedCheckpoint) for(auto &v:row) v=100;
}
int main() {
    reset(); assert(!LoadSequence()); assert(!exists); // no implicit bootstrap
    reset(); VerifiedSequenceFloor=477; assert(LoadSequence()); assert(Sequence==477);
    assert(ReserveNextSequence()); assert(Sequence==478 && gv==478 && disk[0]==478);
    assert(!LoadSequence()); // exclusive handle
    reset(); exists=true; disk={477,-478}; assert(LoadSequence()); // persisted restart
    reset(); exists=true; disk={477,-478}; gv=1; assert(!LoadSequence()); // rollback
    reset(); exists=true; disk={477,-478}; variable=false; assert(!LoadSequence()); // deleted GV
    reset(); exists=true; disk={477,-477}; assert(!LoadSequence()); // torn guard
    reset(); exists=true; disk={477}; assert(!LoadSequence()); // truncated guard
    reset(); VerifiedSequenceFloor=477; PublishedCheckpoint[0][0]=0; assert(!LoadSequence());
    reset(); VerifiedSequenceFloor=0; variable=false; assert(LoadSequence()); assert(Sequence==0);
    reset(); gv=500; VerifiedSequenceFloor=477; assert(!LoadSequence()); assert(!exists);
    reset(); VerifiedSequenceFloor=477; assert(LoadSequence()); gv=0; assert(!ReserveNextSequence()); assert(SequenceFault);
    reset(); VerifiedSequenceFloor=477; assert(LoadSequence()); fail_write=true; assert(!ReserveNextSequence()); assert(gv==477 && SequenceFault);
    reset(); VerifiedSequenceFloor=477; assert(LoadSequence()); Sequence=9007199254740991; gv=(double)Sequence; assert(!ReserveNextSequence());
    reset(); exists=true; disk={477,-478}; PublishedCheckpoint[1][1]=0; assert(!LoadSequence());
    assert(!ValidSequenceValue(std::numeric_limits<double>::quiet_NaN()));
    assert(!ValidSequenceValue(1.5)); assert(!ValidSequenceValue(-1));
    assert(!ValidSequenceValue(9007199254740992.0));
    reset(); assert(!BrokerClockReady()); ticks+=30000; assert(!BrokerClockReady()); // no quote advance
    utc_clock++; broker_clock++; quote_clock++; assert(BrokerClockReady());
    connected=false; assert(!BrokerClockReady()); connected=true; assert(!BrokerClockReady()); // reconnect warms up
    reset(); broker_clock=utc_clock; quote_clock=broker_clock; assert(!BrokerClockReady()); // startup zero offset
    assert(!ValidBrokerClockSample(true,100000,110800,110739,10800)); // stale quote
    assert(!ValidBrokerClockSample(true,100000,110800,110801,10800)); // future quote
    assert(!ValidBrokerClockSample(true,100000,114400,114400,10800)); // offset transition
    assert(ValidBrokerClockSample(true,100000,100000,100000,0)); // verified UTC broker allowed
    assert(BrokerClockSampleReason(false,1,1,1,0)=="TERMINAL_DISCONNECTED");
    assert(BrokerClockSampleReason(true,0,1,1,0)=="CLOCK_OR_QUOTE_UNAVAILABLE");
    assert(BrokerClockSampleReason(true,100000,110800,110739,10800)=="QUOTE_STALE");
    assert(BrokerClockSampleReason(true,100000,110800,110801,10800)=="QUOTE_AHEAD_OF_BROKER_CLOCK");
    assert(BrokerClockSampleReason(true,100000,114400,114400,10800)=="BROKER_UTC_OFFSET_MISMATCH");
    reset(); assert(!BrokerClockReady()); assert(ClockPauseReason=="CLOCK_WARMUP_30_SECONDS");
    ticks+=30000; assert(!BrokerClockReady()); assert(ClockPauseReason=="WAITING_FOR_ADVANCING_QUOTE");
    std::cout << "guard scenarios passed\n";
}
