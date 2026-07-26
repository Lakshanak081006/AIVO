import {useState} from 'react'
import {Link, useNavigate} from 'react-router-dom'
import {useAuth} from '../contexts/AuthContext'
import {ErrorBox} from '../components/Common'

const AUTH_BG = 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200&q=80'

export function Login() {
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('Demo@12345')
  const [error, setError] = useState()
  const {login, loading} = useAuth()
  const nav = useNavigate()
  const submit = async e => {
    e.preventDefault()
    try { await login(email, password); nav('/dashboard') }
    catch(err) { setError(err) }
  }
  return (
    <AuthShell>
      <div className="auth-card">
        <div className="brand" style={{marginBottom:20}}>AIVA<span>Travel Agent</span></div>
        <h1>Welcome back</h1>
        <p className="muted" style={{marginBottom:16}}>Sign in to continue planning</p>
        <form onSubmit={submit}>
          <label>Email<input value={email} onChange={e=>setEmail(e.target.value)} type="email" required/></label>
          <label>Password<input value={password} onChange={e=>setPassword(e.target.value)} type="password" required/></label>
          <ErrorBox error={error}/>
          <button disabled={loading} style={{width:'100%',background:'var(--blue)',color:'#fff',marginTop:8}}>{loading?'Signing in…':'Sign in'}</button>
          <p style={{textAlign:'center',marginTop:16}}>New user? <Link to="/register">Create an account</Link></p>
        </form>
      </div>
    </AuthShell>
  )
}

export function Register() {
  const [form, setForm] = useState({full_name:'', email:'', password:'Strong@123', preferred_language:'English'})
  const [error, setError] = useState()
  const {register} = useAuth()
  const nav = useNavigate()
  const submit = async e => {
    e.preventDefault()
    try { await register(form); nav('/login') }
    catch(err) { setError(err) }
  }
  return (
    <AuthShell>
      <div className="auth-card">
        <div className="brand" style={{marginBottom:20}}>AIVA<span>Travel Agent</span></div>
        <h1>Create your account</h1>
        <p className="muted" style={{marginBottom:16}}>Save plans and personal preferences</p>
        <form onSubmit={submit}>
          {[['full_name','Full name'],['email','Email'],['password','Password']].map(([k,l])=>(
            <label key={k}>{l}
              <input type={k==='password'?'password':k==='email'?'email':'text'} value={form[k]} onChange={e=>setForm({...form,[k]:e.target.value})} required/>
            </label>
          ))}
          <label>Language
            <select value={form.preferred_language} onChange={e=>setForm({...form,preferred_language:e.target.value})}>
              <option>English</option><option>Tamil</option><option>Hindi</option>
            </select>
          </label>
          <ErrorBox error={error}/>
          <button style={{width:'100%',background:'var(--blue)',color:'#fff',marginTop:8}}>Create account</button>
          <p style={{textAlign:'center',marginTop:16}}>Already registered? <Link to="/login">Sign in</Link></p>
        </form>
      </div>
    </AuthShell>
  )
}

function AuthShell({children}) {
  return (
    <div className="auth-page">
      <div className="auth-visual" style={{backgroundImage:`url(${AUTH_BG})`,backgroundSize:'cover',backgroundPosition:'center',position:'relative'}}>
        <div style={{position:'absolute',inset:0,background:'linear-gradient(145deg,#101f4acc,#1a397fcc 60%,#2c65f6aa)'}}/>
        <div style={{position:'relative',zIndex:1,padding:'32px',display:'flex',flexDirection:'column',justifyContent:'flex-end',height:'100%'}}>
          <span className="eyebrow" style={{color:'#a8c4ff'}}>AGENTIC AI TRAVEL PLANNER</span>
          <h2 style={{fontSize:30,margin:'12px 0 8px',color:'#fff',lineHeight:1.2}}>One instruction.<br/>A complete trip plan.</h2>
          <p style={{color:'#c8d8ff',lineHeight:1.7,maxWidth:400}}>Transport, hotels, weather, attractions, itinerary, budget and replanning — all handled autonomously.</p>
          <div style={{display:'flex',gap:12,marginTop:24,flexWrap:'wrap'}}>
            {['🚆 Transport','🏨 Hotels','⛅ Weather','🏛️ Attractions','💰 Budget'].map(t=>(
              <span key={t} style={{background:'#ffffff22',color:'#fff',padding:'6px 12px',borderRadius:20,fontSize:12,fontWeight:600}}>{t}</span>
            ))}
          </div>
        </div>
      </div>
      <div style={{display:'flex',alignItems:'center',justifyContent:'center',padding:'32px 20px',background:'#f4f7fb'}}>
        {children}
      </div>
    </div>
  )
}
