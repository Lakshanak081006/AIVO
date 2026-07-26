import {useEffect, useState} from 'react'
import {api} from '../api/client'
import {ErrorBox} from '../components/Common'

export default function Preferences() {
  const [p, setP] = useState()
  const [error, setError] = useState()
  useEffect(() => {
    api.get('/users/preferences').then(r => setP(r.data.data)).catch(setError)
  }, [])

  if (!p) return <ErrorBox error={error}/>

  const reload = () => api.get('/users/preferences').then(r => setP(r.data.data)).catch(setError)

  const save = async () => {
    try {
      await api.put('/users/preferences', {
        preferred_language: p.preferred_language,
        preferred_currency: p.preferred_currency,
        preferred_transport_type: p.preferred_transport_type || null,
        minimum_hotel_rating: p.minimum_hotel_rating,
        maximum_hotel_distance: p.maximum_hotel_distance,
        preferred_food_type: p.preferred_food_type,
        tourist_interests: p.tourist_interests || [],
        avoid_early_morning: p.avoid_early_morning,
        avoid_late_night: p.avoid_late_night,
        accessibility_requirements: p.accessibility_requirements || [],
      })
      alert('Preferences saved')
    } catch(e) { setError(e) }
  }

  const decide = async (id, decision) => {
    await api.post('/users/preferences/confirm', {suggestion_id: id, decision})
    reload()
  }

  return (
    <>
      {/* Header */}
      <div className="page-hero" style={{backgroundImage:`url(https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1200&q=80)`}}>
        <div className="page-hero-overlay">
          <span className="eyebrow" style={{color:'#a8c4ff'}}>PERSONALISATION</span>
          <h2 style={{margin:'8px 0 6px',color:'#fff',fontSize:28}}>Travel preferences</h2>
          <p style={{color:'#c8d8ff',margin:0}}>AIVA learns from your feedback and suggests preference updates for your approval.</p>
        </div>
      </div>

      <div className="two-col" style={{marginTop:20}}>
        <div className="panel">
          <h3 style={{margin:'0 0 4px'}}>⚙️ Your preferences</h3>
          <p className="muted" style={{margin:'0 0 20px',fontSize:13}}>These are used by all agents when building your plans.</p>

          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0 20px'}}>
            <label>Language
              <select value={p.preferred_language} onChange={e=>setP({...p,preferred_language:e.target.value})}>
                <option>English</option><option>Tamil</option><option>Hindi</option>
              </select>
            </label>
            <label>Currency
              <input value={p.preferred_currency} onChange={e=>setP({...p,preferred_currency:e.target.value.toUpperCase()})}/>
            </label>
            <label>Transport
              <select value={p.preferred_transport_type||''} onChange={e=>setP({...p,preferred_transport_type:e.target.value||null})}>
                <option value="">No preference</option>
                <option>TRAIN</option><option>BUS</option><option>FLIGHT</option><option>CAR</option>
              </select>
            </label>
            <label>Minimum hotel rating
              <input type="number" min="0" max="5" step="0.1" value={p.minimum_hotel_rating||''} onChange={e=>setP({...p,minimum_hotel_rating:e.target.value?Number(e.target.value):null})}/>
            </label>
          </div>

          <div style={{display:'flex',gap:24,margin:'16px 0'}}>
            <label style={{flexDirection:'row',alignItems:'center',gap:10,margin:0}}>
              <input type="checkbox" checked={p.avoid_early_morning} onChange={e=>setP({...p,avoid_early_morning:e.target.checked})} style={{width:'auto'}}/>
              Avoid early morning travel
            </label>
            <label style={{flexDirection:'row',alignItems:'center',gap:10,margin:0}}>
              <input type="checkbox" checked={p.avoid_late_night} onChange={e=>setP({...p,avoid_late_night:e.target.checked})} style={{width:'auto'}}/>
              Avoid late-night travel
            </label>
          </div>

          <ErrorBox error={error}/>
          <button onClick={save} style={{background:'var(--blue)',color:'#fff',width:'100%',padding:'13px'}}>
            💾 Save preferences
          </button>
        </div>

        <div className="panel">
          <h3 style={{margin:'0 0 4px'}}>💡 Suggested preferences</h3>
          <p className="muted" style={{margin:'0 0 20px',fontSize:13}}>Nothing is learned permanently without your approval.</p>

          <div style={{borderRadius:12,overflow:'hidden',marginBottom:20}}>
            <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=70" alt="preferences" style={{width:'100%',height:120,objectFit:'cover'}}/>
          </div>

          {p.pending_suggestions?.filter(x=>x.status==='PENDING').map(x=>(
            <div className="suggestion" key={x.id}>
              <strong style={{textTransform:'capitalize'}}>{x.field.replaceAll('_',' ')}</strong>
              <p style={{margin:'6px 0 4px',fontWeight:600,color:'var(--blue)'}}>{String(x.suggested_value)}</p>
              <small className="muted">{x.reason}</small>
              <div style={{display:'flex',gap:8,marginTop:10}}>
                <button onClick={()=>decide(x.id,'APPROVED')} style={{background:'var(--blue)',color:'#fff',flex:1}}>✓ Approve</button>
                <button className="secondary" onClick={()=>decide(x.id,'REJECTED')} style={{flex:1}}>✗ Reject</button>
              </div>
            </div>
          ))}
          {!p.pending_suggestions?.some(x=>x.status==='PENDING') && (
            <p className="muted" style={{textAlign:'center',padding:'20px 0'}}>No pending suggestions.</p>
          )}
        </div>
      </div>
    </>
  )
}
