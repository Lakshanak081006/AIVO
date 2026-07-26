import {useEffect, useState} from 'react'
import {Link} from 'react-router-dom'
import {api} from '../api/client'
import {StatusBadge, Empty} from '../components/Common'

// Indian city images relevant to the travel planner
const CITY_IMGS = [
  {src:'https://images.unsplash.com/photo-1587474260584-136574528ed5?w=500&q=75', city:'Delhi'},
  {src:'https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=500&q=75', city:'Mumbai'},
  {src:'https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=500&q=75', city:'Chennai'},
  {src:'https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=500&q=75', city:'Bengaluru'},
  {src:'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=500&q=75', city:'Jaipur'},
  {src:'https://images.unsplash.com/photo-1548013146-72479768bada?w=500&q=75', city:'Agra'},
]

export default function Plans() {
  const [plans, setPlans] = useState([])

  useEffect(() => {
    api.get('/travel/plans').then(r => setPlans(r.data.data))
  }, [])

  const remove = async id => {
    if (confirm('Delete this plan?')) {
      await api.delete(`/travel/plans/${id}`)
      api.get('/travel/plans').then(r => setPlans(r.data.data))
    }
  }

  return (
    <>
      {/* Page hero */}
      <div className="page-hero" style={{backgroundImage:`url(https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=1400&q=80)`}}>
        <div className="page-hero-overlay">
          <span className="eyebrow" style={{color:'#a8c4ff'}}>YOUR TRIPS</span>
          <h2 style={{margin:'8px 0 6px',color:'#fff',fontSize:28}}>Saved travel plans</h2>
          <p style={{color:'#c8d8ff',margin:0}}>Review, duplicate, replan or book your generated plans.</p>
        </div>
      </div>

      <div className="panel" style={{marginTop:20}}>
        <div className="panel-title" style={{marginBottom:20}}>
          <div>
            <h3 style={{margin:0}}>All plans</h3>
            <p className="muted" style={{margin:'4px 0 0',fontSize:13}}>
              {plans.length} plan{plans.length !== 1 ? 's' : ''} found
            </p>
          </div>
          <Link className="button" to="/plan/new" style={{background:'var(--blue)',color:'#fff'}}>
            ✈️ New plan
          </Link>
        </div>

        {plans.length ? (
          <div className="plan-grid">
            {plans.map((p, i) => {
              const img = CITY_IMGS[i % CITY_IMGS.length]
              return (
                <div key={p.id} className="plan-card" style={{padding:0,overflow:'hidden',display:'flex',flexDirection:'column'}}>
                  <Link to={`/plans/${p.id}`} style={{display:'block',flex:1}}>
                    <div style={{height:145,overflow:'hidden',borderRadius:'13px 13px 0 0',position:'relative'}}>
                      <img src={img.src} alt={img.city} style={{width:'100%',height:'100%',objectFit:'cover'}}/>
                      <div style={{position:'absolute',inset:0,background:'linear-gradient(to top,#00000066,transparent)'}}/>
                      <div style={{position:'absolute',top:10,left:10}}>
                        <StatusBadge status={p.status}/>
                      </div>
                      <span style={{position:'absolute',bottom:8,right:10,color:'#fff',fontSize:11,fontWeight:700,background:'#00000055',padding:'3px 8px',borderRadius:20}}>
                        📍 {img.city}
                      </span>
                    </div>
                    <div style={{padding:'14px 16px 10px'}}>
                      <h4 style={{margin:'0 0 6px',fontSize:14,lineHeight:1.4}}>{p.title}</h4>
                      <p style={{margin:'0 0 4px',fontWeight:700,color:'var(--blue)',fontSize:15}}>
                        {p.currency} {Number(p.total_cost).toLocaleString()}
                      </p>
                      <small className="muted">Version {p.current_version}</small>
                    </div>
                  </Link>
                  <div style={{padding:'8px 16px 12px',borderTop:'1px solid var(--border)',display:'flex',justifyContent:'flex-end'}}>
                    <button className="text danger" style={{fontSize:12,padding:'4px 8px'}} onClick={() => remove(p.id)}>
                      🗑 Delete
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <Empty text="No plans yet. Create your first autonomous travel plan."/>
        )}
      </div>
    </>
  )
}
