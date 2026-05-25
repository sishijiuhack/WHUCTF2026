package com.example.bocchi_the_reverse;

import android.webkit.JavascriptInterface;

public class NativeVmBridge {

    private static final int TEXT_BASE = 0x0000;

    static {
        System.loadLibrary("nativevm");
    }

    @JavascriptInterface
    public synchronized void resetVm(int blockCount) {
        nativeReset(blockCount);
    }

    @JavascriptInterface
    public int getTextBase() {
        return TEXT_BASE;
    }

    @JavascriptInterface
    public synchronized int getIp() {
        return nativeGetIp();
    }

    @JavascriptInterface
    public synchronized boolean isHalted() {
        return nativeIsHalted();
    }

    @JavascriptInterface
    public synchronized String readInstructionContext(int ip) {
        return nativeReadInstructionContext(ip);
    }

    @JavascriptInterface
    public synchronized void setIp(int ip) {
        nativeSetIp(ip);
    }

    @JavascriptInterface
    public synchronized void setCmp(int cmp) {
        nativeSetCmp(cmp);
    }

    @JavascriptInterface
    public synchronized void setHalted(boolean halted) {
        nativeSetHalted(halted);
    }

    @JavascriptInterface
    public synchronized void setSp(int sp) {
        nativeSetSp(sp);
    }

    @JavascriptInterface
    public synchronized void setRegister(int index, int value) {
        nativeSetRegister(index, value);
    }

    @JavascriptInterface
    public synchronized void setStackValue(int index, int value) {
        nativeSetStackValue(index, value);
    }

    @JavascriptInterface
    public synchronized void writeMemoryU32BE(int addr, int value) {
        nativeWriteMemoryU32BE(addr, value);
    }

    @JavascriptInterface
    public synchronized void writeUtf8ToMemory(int addr, String value) {
        nativeWriteUtf8ToMemory(addr, value);
    }

    @JavascriptInterface
    public synchronized String readMemoryHex(int addr, int len) {
        return nativeReadMemoryHex(addr, len);
    }

    private static native void nativeReset(int blockCount);

    private static native int nativeGetIp();

    private static native boolean nativeIsHalted();

    private static native String nativeReadInstructionContext(int ip);

    private static native void nativeSetIp(int ip);

    private static native void nativeSetCmp(int cmp);

    private static native void nativeSetHalted(boolean halted);

    private static native void nativeSetSp(int sp);

    private static native void nativeSetRegister(int index, int value);

    private static native void nativeSetStackValue(int index, int value);

    private static native void nativeWriteMemoryU32BE(int addr, int value);

    private static native void nativeWriteUtf8ToMemory(int addr, String value);

    private static native String nativeReadMemoryHex(int addr, int len);
}
