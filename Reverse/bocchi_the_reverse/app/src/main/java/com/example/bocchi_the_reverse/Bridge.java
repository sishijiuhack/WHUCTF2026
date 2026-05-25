package com.example.bocchi_the_reverse;

import android.content.Context;
import android.webkit.JavascriptInterface;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public class Bridge {

    private static final int INSTR_SIZE = 8;

    public Bridge(Context context) {
    }

    @JavascriptInterface
    public String nop(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            return nextIpOnly(ctx).toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for NOP", e);
        }
    }

    @JavascriptInterface
    public String halt(String ctxJson) {
        try {
            JSONObject delta = new JSONObject();
            delta.put("halted", true);
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for HALT", e);
        }
    }

    @JavascriptInterface
    public String ldi(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("imm"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for LDI", e);
        }
    }

    @JavascriptInterface
    public String mov(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("srcValue"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for MOV", e);
        }
    }

    @JavascriptInterface
    public String ldwbe(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("value"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for LDWBE", e);
        }
    }

    @JavascriptInterface
    public String stwbe(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addMemoryWrite(delta, ctx.getInt("addr"), ctx.getInt("value"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for STWBE", e);
        }
    }

    @JavascriptInterface
    public String xor(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("lhs") ^ ctx.getInt("rhs"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for XOR", e);
        }
    }

    @JavascriptInterface
    public String xori(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("srcValue") ^ ctx.getInt("imm"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for XORI", e);
        }
    }

    @JavascriptInterface
    public String andi(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("srcValue") & ctx.getInt("imm"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for ANDI", e);
        }
    }

    @JavascriptInterface
    public String shli(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            int shift = ctx.getInt("imm") & 31;
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("srcValue") << shift);
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for SHLI", e);
        }
    }

    @JavascriptInterface
    public String shr(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            int shift = ctx.getInt("imm") & 31;
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("srcValue") >>> shift);
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for SHR", e);
        }
    }

    @JavascriptInterface
    public String roli(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            int shift = ctx.getInt("imm") & 31;
            addRegWrite(delta, ctx.getInt("a"), Integer.rotateLeft(ctx.getInt("srcValue"), shift));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for ROLI", e);
        }
    }

    @JavascriptInterface
    public String addi(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("srcValue") + ctx.getInt("imm"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for ADDI", e);
        }
    }

    @JavascriptInterface
    public String cmp(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            delta.put("cmp", Integer.compare(ctx.getInt("lhs"), ctx.getInt("rhs")));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for CMP", e);
        }
    }

    @JavascriptInterface
    public String jmp(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = new JSONObject();
            delta.put("ip", jumpTarget(ctx));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for JMP", e);
        }
    }

    @JavascriptInterface
    public String jcc(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            int cond = ctx.getInt("a");
            int cmpValue = ctx.getInt("cmpValue");
            boolean take;
            switch (cond) {
                case 0:
                    take = cmpValue == 0;
                    break;
                case 1:
                    take = cmpValue != 0;
                    break;
                case 2:
                    take = cmpValue < 0;
                    break;
                case 3:
                    take = cmpValue <= 0;
                    break;
                case 4:
                    take = cmpValue > 0;
                    break;
                case 5:
                    take = cmpValue >= 0;
                    break;
                default:
                    throw new IllegalStateException("Bad condition: " + cond);
            }
            JSONObject delta = new JSONObject();
            delta.put("ip", take ? jumpTarget(ctx) : nextIp(ctx));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for JCC", e);
        }
    }

    @JavascriptInterface
    public String push(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            int sp = ctx.getInt("sp");
            JSONObject delta = nextIpOnly(ctx);
            delta.put("sp", sp + 1);
            addStackWrite(delta, sp, ctx.getInt("value"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for PUSH", e);
        }
    }

    @JavascriptInterface
    public String pop(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            int nextSp = ctx.getInt("sp") - 1;
            JSONObject delta = nextIpOnly(ctx);
            delta.put("sp", nextSp);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("value"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for POP", e);
        }
    }

    @JavascriptInterface
    public String tbl8(String ctxJson) {
        try {
            JSONObject ctx = new JSONObject(ctxJson);
            JSONObject delta = nextIpOnly(ctx);
            addRegWrite(delta, ctx.getInt("a"), ctx.getInt("value"));
            return delta.toString();
        } catch (JSONException e) {
            throw new IllegalStateException("Invalid ctx for TBL8", e);
        }
    }

    private static int nextIp(JSONObject ctx) throws JSONException {
        return ctx.getInt("ip") + INSTR_SIZE;
    }

    private static int jumpTarget(JSONObject ctx) throws JSONException {
        return ctx.getInt("ip") + INSTR_SIZE + (ctx.getInt("imm") * INSTR_SIZE);
    }

    private static JSONObject nextIpOnly(JSONObject ctx) throws JSONException {
        JSONObject delta = new JSONObject();
        delta.put("ip", nextIp(ctx));
        return delta;
    }

    private static void addRegWrite(JSONObject delta, int index, int value) throws JSONException {
        JSONArray writes = delta.optJSONArray("regWrites");
        if (writes == null) {
            writes = new JSONArray();
            delta.put("regWrites", writes);
        }
        JSONObject write = new JSONObject();
        write.put("index", index);
        write.put("value", value);
        writes.put(write);
    }

    private static void addMemoryWrite(JSONObject delta, int addr, int value) throws JSONException {
        JSONArray writes = delta.optJSONArray("memoryWrites");
        if (writes == null) {
            writes = new JSONArray();
            delta.put("memoryWrites", writes);
        }
        JSONObject write = new JSONObject();
        write.put("addr", addr);
        write.put("value", value);
        writes.put(write);
    }

    private static void addStackWrite(JSONObject delta, int index, int value) throws JSONException {
        JSONArray writes = delta.optJSONArray("stackWrites");
        if (writes == null) {
            writes = new JSONArray();
            delta.put("stackWrites", writes);
        }
        JSONObject write = new JSONObject();
        write.put("index", index);
        write.put("value", value);
        writes.put(write);
    }
}
