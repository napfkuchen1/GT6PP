/* per-draw VS hash pending, 5 instrs */struct VSInput {
    float4 a0:ATTR0;  float4 a1:ATTR1;  float4 a2:ATTR2;  float4 a3:ATTR3;
    float4 a4:ATTR4;  float4 a5:ATTR5;  float4 a6:ATTR6;  float4 a7:ATTR7;
    float4 a8:ATTR8;  float4 a9:ATTR9;  float4 a10:ATTR10; float4 a11:ATTR11;
    float4 a12:ATTR12; float4 a13:ATTR13; float4 a14:ATTR14; float4 a15:ATTR15;
};
struct VSOutput {
    float4 pos:SV_Position; float4 col0:COLOR0; float4 col1:COLOR1;
    float4 fog:FOG;
    float4 t0:TEXCOORD0; float4 t1:TEXCOORD1; float4 t2:TEXCOORD2; float4 t3:TEXCOORD3;
    float4 t4:TEXCOORD4; float4 t5:TEXCOORD5; float4 t6:TEXCOORD6; float4 t7:TEXCOORD7;
    float4 t8:TEXCOORD8; float4 t9:TEXCOORD9;
};
cbuffer VPConst : register(b0) {
    float4 vp_c[512];
    float4 vp_posscale;
    float4 vp_posoffset;
};
float vp_mul1(float a, float b) { return (a == 0.0 || b == 0.0) ? 0.0 : a * b; }
float4 vp_mul(float4 a, float4 b) { return float4(vp_mul1(a.x, b.x), vp_mul1(a.y, b.y), vp_mul1(a.z, b.z), vp_mul1(a.w, b.w)); }
float vp_dot3(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z; }
float vp_dot4(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z + m.w; }
VSOutput main(VSInput input) {
    float4 v[16];
    v[0]=input.a0;  v[1]=input.a1;  v[2]=input.a2;  v[3]=input.a3;
    v[4]=input.a4;  v[5]=input.a5;  v[6]=input.a6;  v[7]=input.a7;
    v[8]=input.a8;  v[9]=input.a9;  v[10]=input.a10; v[11]=input.a11;
    v[12]=input.a12; v[13]=input.a13; v[14]=input.a14; v[15]=input.a15;
    float4 r[32]; float4 o[16];
    [unroll] for (int _i=0;_i<32;_i++) r[_i]=(float4)0;
    [unroll] for (int _j=0;_j<16;_j++) o[_j]=float4(0,0,0,1);
    int4 a0 = (int4)0; int4 a1 = (int4)0;
    float4 cc[2]; cc[0] = (float4)0; cc[1] = (float4)0;
    { float4 _v = (float4)((v[3]).xyzw);
        o[7].xyzw = _v.xyzw;
    }
    { float4 _v = (float4)(vp_dot4(((v[0]).xyzw),((vp_c[3]).xyzw)));
        o[0].w = _v.w;
    }
    { float4 _v = (float4)(vp_dot4(((v[0]).xyzw),((vp_c[2]).xyzw)));
        o[0].z = _v.z;
    }
    { float4 _v = (float4)(vp_dot4(((v[0]).xyzw),((vp_c[1]).xyzw)));
        o[0].y = _v.y;
    }
    { float4 _v = (float4)(vp_dot4(((v[0]).xyzw),((vp_c[0]).xyzw)));
        o[0].x = _v.x;
    }
    VSOutput Out;
    float4 _p = o[0];
    Out.pos = float4(_p.xyz * vp_posscale.xyz + _p.w * vp_posoffset.xyz, _p.w);
    Out.col0 = o[1]; Out.col1 = o[2]; Out.fog = o[5].xxxx;
    Out.t0=o[7];  Out.t1=o[8];  Out.t2=o[9];  Out.t3=o[10];
    Out.t4=o[11]; Out.t5=o[12]; Out.t6=o[13]; Out.t7=o[14];
    Out.t8=o[15]; Out.t9=o[6];
    return Out;
}

/* per-draw VS hash pending, 7 instrs */struct VSInput {
    float4 a0:ATTR0;  float4 a1:ATTR1;  float4 a2:ATTR2;  float4 a3:ATTR3;
    float4 a4:ATTR4;  float4 a5:ATTR5;  float4 a6:ATTR6;  float4 a7:ATTR7;
    float4 a8:ATTR8;  float4 a9:ATTR9;  float4 a10:ATTR10; float4 a11:ATTR11;
    float4 a12:ATTR12; float4 a13:ATTR13; float4 a14:ATTR14; float4 a15:ATTR15;
};
struct VSOutput {
    float4 pos:SV_Position; float4 col0:COLOR0; float4 col1:COLOR1;
    float4 fog:FOG;
    float4 t0:TEXCOORD0; float4 t1:TEXCOORD1; float4 t2:TEXCOORD2; float4 t3:TEXCOORD3;
    float4 t4:TEXCOORD4; float4 t5:TEXCOORD5; float4 t6:TEXCOORD6; float4 t7:TEXCOORD7;
    float4 t8:TEXCOORD8; float4 t9:TEXCOORD9;
};
cbuffer VPConst : register(b0) {
    float4 vp_c[512];
    float4 vp_posscale;
    float4 vp_posoffset;
};
float vp_mul1(float a, float b) { return (a == 0.0 || b == 0.0) ? 0.0 : a * b; }
float4 vp_mul(float4 a, float4 b) { return float4(vp_mul1(a.x, b.x), vp_mul1(a.y, b.y), vp_mul1(a.z, b.z), vp_mul1(a.w, b.w)); }
float vp_dot3(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z; }
float vp_dot4(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z + m.w; }
VSOutput main(VSInput input) {
    float4 v[16];
    v[0]=input.a0;  v[1]=input.a1;  v[2]=input.a2;  v[3]=input.a3;
    v[4]=input.a4;  v[5]=input.a5;  v[6]=input.a6;  v[7]=input.a7;
    v[8]=input.a8;  v[9]=input.a9;  v[10]=input.a10; v[11]=input.a11;
    v[12]=input.a12; v[13]=input.a13; v[14]=input.a14; v[15]=input.a15;
    float4 r[32]; float4 o[16];
    [unroll] for (int _i=0;_i<32;_i++) r[_i]=(float4)0;
    [unroll] for (int _j=0;_j<16;_j++) o[_j]=float4(0,0,0,1);
    int4 a0 = (int4)0; int4 a1 = (int4)0;
    float4 cc[2]; cc[0] = (float4)0; cc[1] = (float4)0;
    { float4 _v = (float4)((v[3]).xyzw);
        o[1].xyzw = _v.xyzw;
    }
    { float4 _v = (float4)((v[0]).xyxx);
        r[0].xy = _v.xy;
    }
    { float4 _v = (float4)((vp_c[467]).xxxx);
        r[0].z = _v.z;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[3]).xyzw))+((vp_c[3]).xyzw).w));
        o[0].w = _v.w;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[2]).xyzw))+((vp_c[2]).xyzw).w));
        o[0].z = _v.z;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[1]).xyzw))+((vp_c[1]).xyzw).w));
        o[0].y = _v.y;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[0]).xyzw))+((vp_c[0]).xyzw).w));
        o[0].x = _v.x;
    }
    VSOutput Out;
    float4 _p = o[0];
    Out.pos = float4(_p.xyz * vp_posscale.xyz + _p.w * vp_posoffset.xyz, _p.w);
    Out.col0 = o[1]; Out.col1 = o[2]; Out.fog = o[5].xxxx;
    Out.t0=o[7];  Out.t1=o[8];  Out.t2=o[9];  Out.t3=o[10];
    Out.t4=o[11]; Out.t5=o[12]; Out.t6=o[13]; Out.t7=o[14];
    Out.t8=o[15]; Out.t9=o[6];
    return Out;
}

/* per-draw VS hash pending, 8 instrs */struct VSInput {
    float4 a0:ATTR0;  float4 a1:ATTR1;  float4 a2:ATTR2;  float4 a3:ATTR3;
    float4 a4:ATTR4;  float4 a5:ATTR5;  float4 a6:ATTR6;  float4 a7:ATTR7;
    float4 a8:ATTR8;  float4 a9:ATTR9;  float4 a10:ATTR10; float4 a11:ATTR11;
    float4 a12:ATTR12; float4 a13:ATTR13; float4 a14:ATTR14; float4 a15:ATTR15;
};
struct VSOutput {
    float4 pos:SV_Position; float4 col0:COLOR0; float4 col1:COLOR1;
    float4 fog:FOG;
    float4 t0:TEXCOORD0; float4 t1:TEXCOORD1; float4 t2:TEXCOORD2; float4 t3:TEXCOORD3;
    float4 t4:TEXCOORD4; float4 t5:TEXCOORD5; float4 t6:TEXCOORD6; float4 t7:TEXCOORD7;
    float4 t8:TEXCOORD8; float4 t9:TEXCOORD9;
};
cbuffer VPConst : register(b0) {
    float4 vp_c[512];
    float4 vp_posscale;
    float4 vp_posoffset;
};
float vp_mul1(float a, float b) { return (a == 0.0 || b == 0.0) ? 0.0 : a * b; }
float4 vp_mul(float4 a, float4 b) { return float4(vp_mul1(a.x, b.x), vp_mul1(a.y, b.y), vp_mul1(a.z, b.z), vp_mul1(a.w, b.w)); }
float vp_dot3(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z; }
float vp_dot4(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z + m.w; }
VSOutput main(VSInput input) {
    float4 v[16];
    v[0]=input.a0;  v[1]=input.a1;  v[2]=input.a2;  v[3]=input.a3;
    v[4]=input.a4;  v[5]=input.a5;  v[6]=input.a6;  v[7]=input.a7;
    v[8]=input.a8;  v[9]=input.a9;  v[10]=input.a10; v[11]=input.a11;
    v[12]=input.a12; v[13]=input.a13; v[14]=input.a14; v[15]=input.a15;
    float4 r[32]; float4 o[16];
    [unroll] for (int _i=0;_i<32;_i++) r[_i]=(float4)0;
    [unroll] for (int _j=0;_j<16;_j++) o[_j]=float4(0,0,0,1);
    int4 a0 = (int4)0; int4 a1 = (int4)0;
    float4 cc[2]; cc[0] = (float4)0; cc[1] = (float4)0;
    { float4 _v = (float4)((v[3]).xyzw);
        o[1].xyzw = _v.xyzw;
    }
    { float4 _v = (float4)((v[8]).xyxx);
        o[7].xy = _v.xy;
    }
    { float4 _v = (float4)((v[0]).xyxx);
        r[0].xy = _v.xy;
    }
    { float4 _v = (float4)((vp_c[467]).xxxx);
        r[0].z = _v.z;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[3]).xyzw))+((vp_c[3]).xyzw).w));
        o[0].w = _v.w;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[2]).xyzw))+((vp_c[2]).xyzw).w));
        o[0].z = _v.z;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[1]).xyzw))+((vp_c[1]).xyzw).w));
        o[0].y = _v.y;
    }
    { float4 _v = (float4)((vp_dot3(((r[0]).xyzx),((vp_c[0]).xyzw))+((vp_c[0]).xyzw).w));
        o[0].x = _v.x;
    }
    VSOutput Out;
    float4 _p = o[0];
    Out.pos = float4(_p.xyz * vp_posscale.xyz + _p.w * vp_posoffset.xyz, _p.w);
    Out.col0 = o[1]; Out.col1 = o[2]; Out.fog = o[5].xxxx;
    Out.t0=o[7];  Out.t1=o[8];  Out.t2=o[9];  Out.t3=o[10];
    Out.t4=o[11]; Out.t5=o[12]; Out.t6=o[13]; Out.t7=o[14];
    Out.t8=o[15]; Out.t9=o[6];
    return Out;
}

/* per-draw VS hash pending, 13 instrs */struct VSInput {
    float4 a0:ATTR0;  float4 a1:ATTR1;  float4 a2:ATTR2;  float4 a3:ATTR3;
    float4 a4:ATTR4;  float4 a5:ATTR5;  float4 a6:ATTR6;  float4 a7:ATTR7;
    float4 a8:ATTR8;  float4 a9:ATTR9;  float4 a10:ATTR10; float4 a11:ATTR11;
    float4 a12:ATTR12; float4 a13:ATTR13; float4 a14:ATTR14; float4 a15:ATTR15;
};
struct VSOutput {
    float4 pos:SV_Position; float4 col0:COLOR0; float4 col1:COLOR1;
    float4 fog:FOG;
    float4 t0:TEXCOORD0; float4 t1:TEXCOORD1; float4 t2:TEXCOORD2; float4 t3:TEXCOORD3;
    float4 t4:TEXCOORD4; float4 t5:TEXCOORD5; float4 t6:TEXCOORD6; float4 t7:TEXCOORD7;
    float4 t8:TEXCOORD8; float4 t9:TEXCOORD9;
};
cbuffer VPConst : register(b0) {
    float4 vp_c[512];
    float4 vp_posscale;
    float4 vp_posoffset;
};
float vp_mul1(float a, float b) { return (a == 0.0 || b == 0.0) ? 0.0 : a * b; }
float4 vp_mul(float4 a, float4 b) { return float4(vp_mul1(a.x, b.x), vp_mul1(a.y, b.y), vp_mul1(a.z, b.z), vp_mul1(a.w, b.w)); }
float vp_dot3(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z; }
float vp_dot4(float4 a, float4 b) { float4 m = vp_mul(a, b); return m.x + m.y + m.z + m.w; }
VSOutput main(VSInput input) {
    float4 v[16];
    v[0]=input.a0;  v[1]=input.a1;  v[2]=input.a2;  v[3]=input.a3;
    v[4]=input.a4;  v[5]=input.a5;  v[6]=input.a6;  v[7]=input.a7;
    v[8]=input.a8;  v[9]=input.a9;  v[10]=input.a10; v[11]=input.a11;
    v[12]=input.a12; v[13]=input.a13; v[14]=input.a14; v[15]=input.a15;
    float4 r[32]; float4 o[16];
    [unroll] for (int _i=0;_i<32;_i++) r[_i]=(float4)0;
    [unroll] for (int _j=0;_j<16;_j++) o[_j]=float4(0,0,0,1);
    int4 a0 = (int4)0; int4 a1 = (int4)0;
    float4 cc[2]; cc[0] = (float4)0; cc[1] = (float4)0;
    { float4 _v = (float4)((v[3]).xyzw);
        o[1].xyzw = _v.xyzw;
    }
    { float4 _v = (float4)((v[8]).xyxx);
        o[7].xy = _v.xy;
    }
    { float4 _v = (float4)((v[0]).xyxx);
        r[1].xy = _v.xy;
    }
    { float4 _v = (float4)((vp_c[466]).xxxx);
        r[1].z = _v.z;
    }
    { float4 _v = (float4)((vp_dot3(((r[1]).xyzx),((vp_c[2]).xyzw))+((vp_c[2]).xyzw).w));
        r[0].z = _v.z;
    }
    { float4 _v = (float4)((vp_dot3(((r[1]).xyzx),((vp_c[3]).xyzw))+((vp_c[3]).xyzw).w));
        r[1].w = _v.w;
    }
    { float4 _v = (float4)((vp_dot3(((r[1]).xyzx),((vp_c[1]).xyzw))+((vp_c[1]).xyzw).w));
        r[0].y = _v.y;
    }
    { float4 _v = (float4)((vp_dot3(((r[1]).xyzx),((vp_c[0]).xyzw))+((vp_c[0]).xyzw).w));
        r[0].x = _v.x;
    }
    { float4 _v = (float4)((1.0/((r[1]).wwww).x));
        r[2].x = _v.x;
    }
    { float4 _v = (float4)((r[1]).wwww);
        r[0].w = _v.w;
    }
    { float4 _v = (float4)(vp_mul(((r[0]).xyxx),((r[2]).xxxx)));
        r[1].xy = _v.xy;
    }
    { float4 _v = (float4)(vp_mul(((r[1]).xyxx),((vp_c[466]).zwzz))+((vp_c[466]).zzzz));
        r[1].xy = _v.xy;
    }
    { float4 _v = (float4)((r[0]).xyzw);
        o[0].xyzw = _v.xyzw;
    }
    { float4 _v = (float4)(vp_mul(((r[1]).xyxx),((vp_c[467]).zwzz))+((vp_c[467]).xyxx));
        o[9].xy = _v.xy;
    }
    VSOutput Out;
    float4 _p = o[0];
    Out.pos = float4(_p.xyz * vp_posscale.xyz + _p.w * vp_posoffset.xyz, _p.w);
    Out.col0 = o[1]; Out.col1 = o[2]; Out.fog = o[5].xxxx;
    Out.t0=o[7];  Out.t1=o[8];  Out.t2=o[9];  Out.t3=o[10];
    Out.t4=o[11]; Out.t5=o[12]; Out.t6=o[13]; Out.t7=o[14];
    Out.t8=o[15]; Out.t9=o[6];
    return Out;
}

