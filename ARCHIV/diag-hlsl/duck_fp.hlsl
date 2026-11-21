/* fp_addr=0x04E52DC1, 9 instrs */struct PSInput {
    float4 position : SV_POSITION; float4 col0 : COLOR0; float4 col1 : COLOR1;
    float4 fog : FOG;
    float4 tc0:TEXCOORD0; float4 tc1:TEXCOORD1; float4 tc2:TEXCOORD2; float4 tc3:TEXCOORD3;
    float4 tc4:TEXCOORD4; float4 tc5:TEXCOORD5; float4 tc6:TEXCOORD6; float4 tc7:TEXCOORD7;
};
Texture2D    rsx_tex[16] : register(t0);
SamplerState rsx_samp[16] : register(s0);
float4 main(PSInput input) : SV_TARGET {
    float4 r[48]; float4 h[48];
    [unroll] for (int _i = 0; _i < 48; _i++) { r[_i] = (float4)0; h[_i] = (float4)0; }
    float4 cc0 = (float4)0; float4 cc1 = (float4)0;
    { float4 _v = (float4)(((input.tc2).zwzz) + (-((float4(378,213,374,209)).xyxx))); r[0].xy = _v.xy; }
    { float4 _v = (float4)((abs((r[0]).xyzw)) + (-((float4(378,213,374,209)).zwzz))); r[0].xy = _v.xy; }
    { float4 _v = (float4)(max(((r[0]).xyzw), ((float4(0,0,0,0)).xxxx))); r[0].xy = _v.xy; }
    { float4 _v = (float4)(dot(((r[0]).xyzw).xy, ((r[0]).xyzw).xy)); r[0].x = _v.x; }
    { float4 _v = (float4)((abs(abs((r[0]).xyzw)) > 0.0 ? (abs((r[0]).xyzw)) / sqrt(abs(((r[0]).xyzw).x)) : (float4)0.0)); r[0].x = _v.x; }
    { float4 _v = (float4)((-((r[0]).xxxx)) + ((float4(3.5,4.5,0,0)).yyyy)); _v = saturate(_v); r[0].z = _v.z; }
    { float4 _v = (float4)((saturate(input.col0)).xyzw); h[0].xyzw = _v.xyzw; }
    { float4 _v = (float4)((h[0]).xyzw); h[0].xyz = _v.xyz; }
    { float4 _v = (float4)(((h[0]).xyzw) * ((r[0]).zzzz)); h[0].w = _v.w; }
    float4 _o = h[0];
    return (_o == _o) ? _o : (float4)0;
}
