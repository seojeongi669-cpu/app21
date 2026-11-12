"""숨틈 · 금연 동행 — streamlit run quit_app.py
GitHub에 이 파일과 requirements.txt 업로드 → Streamlit Cloud 실행 파일 quit_app.py.
기본 저장: 로컬 SQLite. Cloud 재배포·서버 초기화 시 사라질 수 있습니다.
영구 저장 선택: Supabase SQL Editor에서 아래 실행:
create table public.quit_accounts (id text primary key,payload jsonb not null,version integer not null default 0);
alter table public.quit_accounts enable row level security;
-- 공개 접근 정책을 추가하지 마세요. 서버만 접근합니다.
Streamlit Settings > Secrets (키를 GitHub에 올리지 마세요):
SUPABASE_URL="https://프로젝트.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="서버 전용 service_role 키"
정보 출처: 국가금연지원서비스 https://nosmokeguide.go.kr / 금연상담전화 1544-9030
건강 회복 시점·수명 연장 등의 개인별 의학 수치를 추정하지 않습니다.
"""
import streamlit as st
import streamlit.config as config
import requests,sqlite3,json,secrets,hashlib,time,html
from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
for k,v in {'theme.base':'light','theme.primaryColor':'#277666','theme.backgroundColor':'#F5F8F4','theme.secondaryBackgroundColor':'#FFFFFF','theme.textColor':'#243D36'}.items():
    config.set_option(k,v)
st.set_page_config(page_title='숨틈 · 금연 동행',page_icon='🌿',layout='centered')
TZ=ZoneInfo('Asia/Seoul')
def now(): return datetime.now(TZ)
def hashed(s):return hashlib.sha256(s.encode()).hexdigest()
def pw(p,s):return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),180000).hex()
def remote():
    try:return bool(st.secrets.get('SUPABASE_URL') and st.secrets.get('SUPABASE_SERVICE_ROLE_KEY'))
    except Exception:return False
def db(key,data=None,version=None):
    if remote():
        root=st.secrets['SUPABASE_URL'].rstrip('/')+'/rest/v1/quit_accounts'
        headers={'apikey':st.secrets['SUPABASE_SERVICE_ROLE_KEY'],'Authorization':'Bearer '+st.secrets['SUPABASE_SERVICE_ROLE_KEY'],'Prefer':'return=representation'}
        if data is None:
            r=requests.get(root,params={'id':'eq.'+key},headers=headers,timeout=20);r.raise_for_status();rows=r.json()
            return (rows[0]['payload'],rows[0]['version']) if rows else (None,None)
        if version is None:
            r=requests.post(root,headers=headers,json={'id':key,'payload':data,'version':0},timeout=20)
        else:
            r=requests.patch(root,params={'id':'eq.'+key,'version':'eq.'+str(version)},headers=headers,json={'payload':data,'version':version+1},timeout=20)
        r.raise_for_status()
        if not r.json():raise ValueError('다른 화면에서 변경됐어요. 새로고침 후 다시 해 주세요.')
        return
    with sqlite3.connect('quit_data.sqlite3',timeout=20) as c:
        c.execute('create table if not exists accounts(id text primary key,payload text,version integer not null)')
        if data is None:
            row=c.execute('select payload,version from accounts where id=?',(key,)).fetchone()
            return (json.loads(row[0]),row[1]) if row else (None,None)
        if version is None:c.execute('insert into accounts values(?,?,0)',(key,json.dumps(data)))
        else:
            q=c.execute('update accounts set payload=?,version=version+1 where id=? and version=?',(json.dumps(data),key,version))
            if q.rowcount!=1:raise ValueError('다른 화면에서 변경됐어요. 새로고침 후 다시 해 주세요.')
def save(d,v):db(st.session_state.uid,d,v);st.rerun()
def elapsed(start,end):return max(0,(end-start).total_seconds())
def estimates(start,end,cigs,price,pack):
    days=elapsed(start,end)/86400
    return days*cigs,days*cigs*price/pack
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
:root{color-scheme:light!important} .stApp{background:#F5F8F4!important;color:#243D36!important}
.block-container{max-width:650px;padding:1.4rem 1rem 3rem}
[data-testid="stHeader"]{background:transparent}
h1,h2,h3{font-family:'Jua',sans-serif!important;letter-spacing:-.5px}
input,textarea,[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="select"]>div{background:white!important;color:#243D36!important;-webkit-text-fill-color:#243D36!important}
[data-testid="stNumberInput"] button{background:#ECF3ED!important;color:#243D36!important}
[role="dialog"],[role="listbox"],[data-baseweb="calendar"]{background:white!important;color:#243D36!important}
button{border-radius:14px!important} [data-testid="stForm"]{background:white;border-radius:20px;border-color:#DEE8DE}
.hero{background:#E3EEE2;border-radius:25px;padding:25px;margin-bottom:18px;border:1px solid #CDDCCB}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:2px;color:#42654F}.title{font-family:'Jua',sans-serif;font-size:36px;color:#254E3F;line-height:1.2;margin:9px 0}.sub{font-size:15px;color:#426052}
.chip{display:inline-block;background:#FFFDF6;border-radius:30px;padding:5px 12px;font-size:12px;color:#49624E;margin-top:14px}
.counter{background:#244E40;color:#FFFDF2;border-radius:23px;padding:24px;text-align:center;margin:12px 0}.counter small{color:#D5E8D5}.counter strong{display:block;font-size:38px;font-family:'Jua',sans-serif;margin:8px 0}
[data-testid="stMetric"]{background:white;border:1px solid #DDE7DD;padding:12px;border-radius:17px}[data-testid="stMetricLabel"]{color:#466154}
[role="radiogroup"]{gap:8px;background:#EAF0E7;padding:9px;border-radius:15px}
</style>''',unsafe_allow_html=True)
try:
    if 'uid' not in st.session_state:
        st.markdown('<div class="hero"><div class="eyebrow">A LITTLE BREATH, A NEW START</div><div class="title">금연, 혼자 참지 말고<br>하루씩 함께해요 🌿</div><div class="sub">숨틈 · 금연 시간과 절약 기록, 흡연 욕구 대처까지</div><div class="chip">이메일 없이 · 나만의 기록</div></div>',unsafe_allow_html=True)
        tab=st.radio('계정',['로그인','회원가입','계정 복구'],horizontal=True,label_visibility='collapsed')
        if st.session_state.get('recovery'):
            st.success('가입 완료! 복구 코드를 안전한 곳에 보관한 뒤 로그인하세요.')
            st.code(st.session_state.recovery)
            st.caption('코드를 아는 사람은 계정을 복구할 수 있어요. 공유하지 마세요.')
        with st.form('auth'):
            if tab=='계정 복구':
                code=st.text_input('복구 코드',type='password');new=st.text_input('새 비밀번호 (8자 이상)',type='password')
            else:
                username=st.text_input('아이디',placeholder='영문·숫자·밑줄 3~30자',max_chars=30).strip().lower()
                password=st.text_input('비밀번호 (8자 이상)',type='password')
                confirm=st.text_input('비밀번호 확인',type='password') if tab=='회원가입' else password
            submit=st.form_submit_button(tab,type='primary',use_container_width=True)
        if submit:
            if tab=='계정 복구':
                entry,_=db('recovery_'+hashed(code.strip().upper()))
                if not entry or len(new)<8:st.error('복구 코드와 비밀번호를 확인해 주세요.')
                else:
                    d,v=db(entry['uid']);d['salt']=secrets.token_hex(16);d['password']=pw(new,d['salt']);db(entry['uid'],d,v)
                    st.success('아이디: '+d['username']+' · 비밀번호를 변경했어요. 로그인해 주세요.')
            elif not (3<=len(username)<=30 and all(x.isascii() and (x.isalnum() or x=='_') for x in username)) or len(password)<8 or confirm!=password:
                st.error('아이디 형식과 비밀번호를 확인해 주세요.')
            else:
                uid='user_'+hashed(username);d,v=db(uid)
                if tab=='회원가입':
                    if d:st.error('이미 사용 중인 아이디예요.')
                    else:
                        salt=secrets.token_hex(16);recovery=secrets.token_hex(16).upper()
                        db(uid,{'username':username,'salt':salt,'password':pw(password,salt),'profile':None,'cravings':[],'slips':[],'checks':[]})
                        db('recovery_'+hashed(recovery),{'uid':uid})
                        st.session_state.recovery=recovery;st.rerun()
                elif d and secrets.compare_digest(d['password'],pw(password,d['salt'])):
                    st.session_state.uid=uid;st.session_state.pop('recovery',None);st.rerun()
                else:st.error('아이디 또는 비밀번호를 확인해 주세요.')
        if not remote():st.caption('체험 저장: 서버 초기화 시 기록이 사라질 수 있어요. 영구 저장 설정은 파일 맨 위를 확인하세요.')
        st.stop()
    d,v=db(st.session_state.uid)
    if not d:st.session_state.clear();st.rerun()
    st.markdown('### 🌿 숨틈 · 금연 동행')
    menu=st.radio('메뉴',['오늘','욕구 대처','나의 기록','설정'],horizontal=True,label_visibility='collapsed')
    if d['profile'] is None or menu=='설정':
        st.subheader('나에게 맞는 금연 시작')
        with st.form('profile'):
            p=d['profile'] or {'start':now().isoformat(),'cigs':10,'price':4500,'pack':20,'reason':''}
            start=datetime.fromisoformat(p['start'])
            c1,c2=st.columns(2)
            day=c1.date_input('금연 시작일',start.date(),max_value=now().date()+timedelta(days=365))
            tm=c2.time_input('시작 시각',start.time().replace(tzinfo=None))
            cigs=st.number_input('금연 전 하루 평균 흡연 개비',1,200,int(p['cigs']))
            c1,c2=st.columns(2);price=c1.number_input('한 갑 가격 (원)',100,100000,int(p['price']),100);pack=c2.number_input('한 갑의 개비 수',1,100,int(p['pack']))
            reason=st.text_input('금연하고 싶은 이유',p['reason'],placeholder='예: 가족과 오래 건강하게 지내고 싶어서',max_chars=100)
            ok=st.form_submit_button('저장하고 시작',type='primary',use_container_width=True)
        if ok:
            d['profile']={'start':datetime.combine(day,tm,TZ).isoformat(),'cigs':cigs,'price':price,'pack':pack,'reason':reason};save(d,v)
        if menu=='설정':
            st.download_button('내 기록 백업',json.dumps(d,ensure_ascii=False,indent=2),file_name='숨틈_개인백업.json',mime='application/json')
            st.caption('백업에는 민감한 개인 기록과 인증용 해시가 포함돼요. 공유하지 마세요. 자동 복원 기능은 없어요.')
            if st.button('로그아웃'):st.session_state.clear();st.rerun()
        if not remote():st.warning('지금은 임시 체험 저장이에요. 재배포 전 기록을 백업하세요.')
        st.stop()
    p=d['profile'];start=datetime.fromisoformat(p['start']);current=now()
    future=start>current
    if menu=='오늘':
        @st.fragment(run_every='30s')
        def live():
            n=now();seconds=elapsed(start,n);days=int(seconds//86400);hours=int(seconds%86400//3600);minutes=int(seconds%3600//60)
            if start>n:
                st.info('금연 시작 예정: '+start.strftime('%Y.%m.%d %H:%M'));return
            st.markdown(f'<div class="counter"><small>금연 시작 후 경과 · 한국 시간</small><strong>{days}일 {hours}시간 {minutes}분</strong><small>완벽한 하루보다, 이어가는 하루</small></div>',unsafe_allow_html=True)
            avoided,money=estimates(start,n,p['cigs'],p['price'],p['pack'])
            smoked=sum(x['count'] for x in d['slips'] if start<=datetime.fromisoformat(x['at'])<=n)
            c1,c2=st.columns(2);c1.metric('예상 절약',f'{max(0,money-smoked*p["price"]/p["pack"]):,.0f}원');c2.metric('예상 줄인 흡연',f'{max(0,avoided-smoked):,.1f}개비')
        live()
        st.caption('금연 전 평균과 입력한 흡연 기록을 이용한 추정치이며 실제 절약액과 다를 수 있어요.')
        if p['reason']:st.info('💚 나의 이유 · '+p['reason'])
        if not future:
            checked=str(current.date()) in d['checks']
            if st.button('✓ 오늘 금연 실천 기록'+(' 완료' if checked else ''),disabled=checked,type='primary',use_container_width=True):
                d['checks'].append(str(current.date()));save(d,v)
            st.caption('실천 체크는 하루 한 번. 흡연한 날도 숨기지 않고 기록할 수 있어요.')
        with st.expander('한 번 피웠다면? 자책 대신 다시 이어가기'):
            st.write('한 번의 흡연이 그동안의 노력을 지우지는 않아요. 상황을 기록하고 다음 대처를 정해 보세요.')
            with st.form('slip'):
                count=st.number_input('지금 기록할 흡연 개비',1,100,1);note=st.text_input('상황 메모',max_chars=150)
                slip=st.form_submit_button('흡연 기록 남기기',disabled=future)
            if slip:d['slips'].append({'at':now().isoformat(),'count':count,'note':note});save(d,v)
            st.caption('경과 시간은 금연 시도 시작 기준이며 연속 금연 인증이 아니에요. 새 시작은 설정에서 날짜를 변경하세요.')
        st.markdown('[금연길라잡이 · 공식 도움 받기](https://nosmokeguide.go.kr)')
        st.caption('금연상담전화 1544-9030 · 흉통이나 심한 호흡곤란 등 응급상황은 119')
    elif menu=='욕구 대처':
        st.subheader('담배 생각이 날 때, 잠깐의 숨틈')
        trigger=st.selectbox('지금 어떤 상황인가요?',['스트레스','식후','커피·술자리','주변 사람이 흡연','심심함','기타'])
        intensity=st.select_slider('지금 욕구 강도',options=list(range(1,11)),value=5)
        advice={'스트레스':'자리에서 잠깐 벗어나 어깨를 풀고 편안하게 숨 쉬어 보세요.','식후':'식사를 마쳤다면 양치하거나 짧게 걸어 보세요.','커피·술자리':'가능하면 흡연을 떠올리게 하는 자리를 잠시 피하고 물을 마셔 보세요.','주변 사람이 흡연':'금연 중이라고 알리고 담배 연기가 없는 곳으로 이동해 보세요.','심심함':'손으로 할 수 있는 짧은 일이나 가벼운 산책을 골라 보세요.','기타':'지금 감정을 짧게 적고, 신뢰하는 사람에게 도움을 요청해 보세요.'}
        st.info(advice[trigger])
        c1,c2=st.columns(2)
        if c1.button('3분 쉬어가기',use_container_width=True):st.session_state.pause_end=time.time()+180
        if c2.button('욕구 기록',type='primary',use_container_width=True):
            d['cravings'].append({'at':now().isoformat(),'trigger':trigger,'intensity':intensity});save(d,v)
        @st.fragment(run_every='1s')
        def pause():
            end=st.session_state.get('pause_end')
            if end:
                left=max(0,int(end-time.time()));st.metric('잠시 쉬어가는 시간',f'{left//60:02}:{left%60:02}')
                if left==0:st.success('잠깐 멈췄어요. 지금 기분을 다시 살펴보세요.')
                else:st.caption('편안하게 호흡하세요. 어지럽거나 불편하면 중단하세요. 소리 알림은 없어요.')
        pause()
        st.caption('참기 어렵거나 금단 증상으로 힘들면 금연상담전화 1544-9030 또는 의료진과 상의하세요. 약물·니코틴 대체요법은 전문가와 상담하세요.')
    else:
        st.subheader('나의 변화, 판단 없이 기록하기')
        week=current.date()-timedelta(days=6)
        c1,c2=st.columns(2);c1.metric('최근 7일 실천 체크',sum(week<=date.fromisoformat(x)<=current.date() for x in d['checks']));c2.metric('최근 7일 욕구 기록',sum(week<=datetime.fromisoformat(x['at']).date()<=current.date() for x in d['cravings']))
        if d['cravings']:
            counts={}
            for x in d['cravings']:counts[x['trigger']]=counts.get(x['trigger'],0)+1
            st.info('가장 자주 기록한 상황: '+max(counts,key=counts.get)+' · 다음에는 미리 대처를 준비해 보세요.')
        entries=[{'at':x['at'],'text':f"욕구 {x['intensity']}/10 · {x['trigger']}",'kind':'cravings','i':i} for i,x in enumerate(d['cravings'])]+[{'at':x['at'],'text':f"흡연 {x['count']}개비 · {x['note']}",'kind':'slips','i':i} for i,x in enumerate(d['slips'])]
        for x in sorted(entries,key=lambda x:x['at'],reverse=True)[:30]:
            c1,c2=st.columns([5,1]);c1.write(datetime.fromisoformat(x['at']).strftime('%m/%d %H:%M')+' · '+x['text'])
            if c2.button('삭제',key=x['kind']+str(x['i'])):d[x['kind']].pop(x['i']);save(d,v)
        if not entries:st.caption('욕구 대처 메뉴에서 첫 기록을 남겨 보세요.')
        if d['checks']:
            with st.expander('잘못 누른 실천 체크 취소'):
                day=st.selectbox('날짜',sorted(d['checks'],reverse=True))
                if st.button('선택 날짜 체크 취소'):d['checks'].remove(day);save(d,v)
except (requests.RequestException,sqlite3.Error,ValueError,KeyError,TypeError) as e:
    st.error('연결 또는 저장에 문제가 생겼어요. 새로고침 후 다시 시도해 주세요. 계속되면 저장소 설정을 확인하세요.')
