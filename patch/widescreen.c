/* Original adaptation code. MIT license. D3D8 ABI, no Windows SDK or CRT. */
typedef unsigned int U;
typedef unsigned long long Q;
typedef int H;
#define S __attribute__((stdcall))
#define V(o,n) (*(void***)(o))[n]
typedef H(S *SetT)(void*,U,const float*);
typedef H(S *DrawUP)(void*,U,U,const void*,U);
typedef H(S *DrawI)(void*,U,U,U,U,U);
typedef H(S *GetU)(void*,U*);
typedef H(S *GetStream)(void*,U,void**,U*);
typedef H(S *GetIndices)(void*,void**,U*);
typedef H(S *Lock)(void*,U,U,void**,U);
typedef H(S *Unary)(void*);
typedef H(S *DrawIUP)(void*,U,U,U,U,const void*,U,const void*,U);

volatile Q pause_cycles, pause_qpc;
volatile U pause_millis;
volatile U save_request,save_done,save_ok;
static unsigned char scratch[2097152];
static void copy(void*d,const void*s,U n){
    unsigned char*a=d; const unsigned char*b=s;
    while(n--)*a++=*b++;
}
static U vertices(U t,U n){return t==1?n:t==2?n*2:t==3?n+1:t==4?n*3:n+2;}
static H pretransformed(U f){return (f&15)==4 && !(f&0x80000000);}
static void scale(void*p,U n,U stride){
    for(U i=0;i<n;i++){
        float*v=(float*)((char*)p+i*stride);
        v[0]=v[0]*2.25f+240.0f;
        v[1]*=2.25f;
    }
}

/* Keep the engine's 640x480 logical UI; enlarge only the backbuffer. */
H S create_device(void*d,U adapter,U type,U window,U flags,U*pp,void**out){
    pp[0]=1920; pp[1]=1080;
    return ((H(S*)(void*,U,U,U,U,U*,void**))V(d,15))(d,adapter,type,window,flags,pp,out);
}
__asm__(".global create_primary\ncreate_primary:\ncall create_device\nmov %eax,%esi\npush $0x4797d9\nret\n"
        ".global create_retry\ncreate_retry:\ncall create_device\nmov %eax,%esi\npush $0x4798cc\nret\n");

H S projection(void*d,U state,const float*m){
    if(save_request!=save_done && *(U*)0x5ab0b0==3 && *(char*)0x5b2ab8 && *(char*)0x5b2ac3){
        save_ok=((H(*)(void*))0x4659b0)((void*)0x5b2ab8);
        save_done=save_request;
    }
    /* The game reloads this matrix before each call. Updating it also fixes
       CPU culling and the programmable shaders fed immediately afterwards. */
    if(state==3){float*q=(float*)m;for(U i=0;i<4;i++)q[i*4]*=.75f;}
    return ((SetT)V(d,37))(d,state,m);
}
H S viewport(void*d,const U*v){
    U q[6];copy(q,v,24);
    q[0]*=3;q[1]=q[1]*9/4;q[2]*=3;q[3]=q[3]*9/4;
    return ((H(S*)(void*,const U*))V(d,40))(d,q);
}
H S draw_up(void*d,U type,U n,const void*p,U stride){
    U f=0;((GetU)V(d,77))(d,&f);
    U c=vertices(type,n);
    if(pretransformed(f)&&stride>=16&&c<=sizeof(scratch)/stride){
        copy(scratch,p,c*stride);scale(scratch,c,stride);
        return ((DrawUP)V(d,72))(d,type,n,scratch,stride);
    }
    return ((DrawUP)V(d,72))(d,type,n,p,stride);
}
H S draw_indexed(void*d,U type,U min,U num,U start,U n){
    U f=0;((GetU)V(d,77))(d,&f);
    if(pretransformed(f)){
        void*vb=0,*ib=0,*vp=0,*ip=0;
        U stride=0,base=0,id[6]={0},vd[6]={0};H result;
        ((GetStream)V(d,84))(d,0,&vb,&stride);
        ((GetIndices)V(d,86))(d,&ib,&base);
        if(vb&&ib&&stride>=16&&min+num>=min&&(min+num)<=sizeof(scratch)/stride){
            ((H(S*)(void*,U*))V(ib,13))(ib,id);
            ((H(S*)(void*,U*))V(vb,13))(vb,vd);
            U count=vertices(type,n),ibytes=id[0]==102?4:2;
            if((Q)(base+min+num)*stride<=vd[4] && (Q)(start+count)*ibytes<=id[4]
               && ((Lock)V(vb,11))(vb,0,0,&vp,16)==0){
                copy(scratch,(char*)vp+base*stride,(min+num)*stride);
                ((Unary)V(vb,12))(vb);scale(scratch,min+num,stride);
                if(((Lock)V(ib,11))(ib,0,0,&ip,16)==0){
                    result=((DrawIUP)V(d,73))(d,type,min,num,n,(char*)ip+start*ibytes,id[0],scratch,stride);
                    ((Unary)V(ib,12))(ib);
                    /* UP clears bindings. Restore both before returning. */
                    ((H(S*)(void*,U,void*,U))V(d,83))(d,0,vb,stride);
                    ((H(S*)(void*,void*,U))V(d,85))(d,ib,base);
                    ((Unary)V(vb,2))(vb);((Unary)V(ib,2))(ib);return result;
                }
            }
        }
        if(vb)((Unary)V(vb,2))(vb);
        if(ib)((Unary)V(ib,2))(ib);
    }
    return ((DrawI)V(d,71))(d,type,min,num,start,n);
}
H S query_counter(Q*out){
    H result=((H(S*)(Q*))(*(U*)0x36500f4))(out);
    if(result)*out-=pause_qpc;
    return result;
}
U S tick_count(void){return ((U(S*)(void))(*(U*)0x365013c))()-pause_millis;}
