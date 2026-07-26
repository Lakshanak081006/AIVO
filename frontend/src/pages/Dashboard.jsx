import {useEffect, useState} from 'react'
import {Link} from 'react-router-dom'
import {api} from '../api/client'
import {StatusBadge, Empty} from '../components/Common'
import {useAuth} from '../contexts/AuthContext'

const HERO_BG = 'https://images.unsplash.com/photo-1530521954074-e64f6810b32d?w=1400&q=80'
const PLAN_IMGS = [
  'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400&q=70',
  'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&q=70',
  'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=400&q=70',
  'https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=400&q=70',
]

export default function Dashboard() {
  const {user} = useAuth()
  const [plans, setPlans] = useState([])
  useEffect(() => {
    api.get('/travel/plans').then(r => setPlans(r.data.data))
  }, [])
  const ready = plans.filter(p => p.status === 'READY' || p.status === 'BOOKED').length

  return (
    <>
      {/* Hero banner */}
      <div className="dash-hero" style={{backgroundImage:`url(${HERO_BG})`}}>
        <div className="dash-hero-overlay">
          <span className="eyebrow" style={{color:'#a8c4ff'}}>AGENTIC AI</span>
          <h2>Hello, {user?.full_name?.split(' ')[0]}. Where next?</h2>
          <p>Describe one goal. Multiple specialized agents build and validate the complete plan.</p>
          <Link className="button" to="/plan/new" style={{background:'#fff',color:'#173274',marginTop:8}}>
            ✈️ Plan a new trip
          </Link>
        </div>
        <div className="agent-orbit" style={{marginRight:40}}>
          AI
          <div>Transport</div>
          <div>Hotel</div>
          <div>Weather</div>
          <div>Budget</div>
        </div>
      </div>

      {/* Stats */}
      <div className="stats">
        <Stat icon="🗺️" label="Total plans" value={plans.length}/>
        <Stat icon="✅" label="Ready plans" value={ready}/>
        <Stat icon="🤖" label="Agent modules" value="10"/>
        <Stat icon="🌐" label="Languages" value="3"/>
      </div>

      {/* Recent plans */}
      <div className="panel">
        <div className="panel-title">
          <div>
            <h3 style={{margin:0}}>Recent plans</h3>
            <p className="muted" style={{margin:'4px 0 0',fontSize:13}}>Your latest autonomous travel plans</p>
          </div>
          <Link to="/plans" className="button" style={{fontSize:13}}>View all</Link>
        </div>
        {plans.length ? (
          <div className="plan-grid" style={{marginTop:18}}>
            {plans.slice(0, 4).map((p, i) => (
              <Link className="plan-card" key={p.id} to={`/plans/${p.id}`} style={{overflow:'hidden',padding:0,display:'block'}}>
                <div style={{height:130,overflow:'hidden',borderRadius:'13px 13px 0 0'}}>
                  <img src={PLAN_IMGS[i % PLAN_IMGS.length]} alt="destination" style={{width:'100%',height:'100%',objectFit:'cover'}}/>
                </div>
                <div style={{padding:'14px 16px'}}>
                  <StatusBadge status={p.status}/>
                  <h4 style={{margin:'8px 0 4px',fontSize:14}}>{p.title}</h4>
                  <p style={{margin:0,fontWeight:700,color:'var(--blue)'}}>{p.currency} {Number(p.total_cost).toLocaleString()}</p>
                  <small className="muted">Version {p.current_version}</small>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <Empty text="Create your first autonomous travel plan."/>
        )}
      </div>

      {/* Travel inspiration */}
      <div className="panel">
        <div className="panel-title">
          <h3 style={{margin:0}}>Travel inspiration</h3>
        </div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:12,marginTop:16}}>
          {[
            {img:'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=500&q=75',label:'Delhi'},
            {img:'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=500&q=75',label:'Mumbai'},
            {img:'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=500&q=75',label:'Chennai'},
            {img:'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=500&q=75',label:'Jaipur'},
          ].map(d=>(
            <div key={d.label} style={{borderRadius:12,overflow:'hidden',position:'relative',height:120,cursor:'pointer'}}>
              <img src={d.img} alt={d.label} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
              <div style={{position:'absolute',inset:0,background:'linear-gradient(to top,#00000088,transparent)',display:'flex',alignItems:'flex-end',padding:'10px 12px'}}>
                <span style={{color:'#fff',fontWeight:700,fontSize:14}}>{d.label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

function Stat({icon, label, value}) {
  return (
    <div className="stat" style={{display:'flex',alignItems:'center',gap:14}}>
      <span style={{fontSize:28}}>{icon}</span>
      <div>
        <strong style={{fontSize:26,display:'block'}}>{value}</strong>
        <span className="muted" style={{fontSize:12}}>{label}</span>
      </div>
    </div>
  )
}
