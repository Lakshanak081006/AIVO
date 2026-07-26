import {Link} from 'react-router-dom'

const HERO_IMG = 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1400&q=80'
const DEST_IMGS = [
  {src:'https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=600&q=80', label:'India'},
  {src:'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80', label:'Europe'},
  {src:'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&q=80', label:'Mountains'},
  {src:'https://images.unsplash.com/photo-1519046904884-53103b34b206?w=600&q=80', label:'Beaches'},
]

export default function Landing() {
  return (
    <div className="landing">
      <nav>
        <div className="brand">AIVA<span>Travel Agent</span></div>
        <div style={{display:'flex',gap:12,alignItems:'center'}}>
          <Link to="/login">Sign in</Link>
          <Link className="button" to="/register">Get started</Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="landing-hero" style={{backgroundImage:`url(${HERO_IMG})`}}>
        <div className="landing-hero-overlay">
          <span className="eyebrow" style={{color:'#a8c4ff'}}>AUTONOMOUS PERSONAL ASSISTANT</span>
          <h1>One travel goal.<br/><em>Every step handled.</em></h1>
          <p>An Agentic AI system that decomposes your request, runs specialized agents in parallel, controls the budget, recovers from failures and explains every decision.</p>
          <div className="landing-actions">
            <Link className="button" to="/login">Try the demo</Link>
            <a href="http://localhost:8000/docs" style={{color:'#fff',fontWeight:600}}>Open API docs →</a>
          </div>
        </div>
      </div>

      {/* Destinations strip */}
      <div className="landing-section">
        <span className="eyebrow">POPULAR DESTINATIONS</span>
        <h2 style={{margin:'10px 0 24px'}}>Plan trips anywhere</h2>
        <div className="dest-grid">
          {DEST_IMGS.map(d=>(
            <div className="dest-card" key={d.label}>
              <img src={d.src} alt={d.label}/>
              <span>{d.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Features */}
      <div className="landing-section landing-features-bg">
        <span className="eyebrow">WHAT AIVA DOES</span>
        <h2 style={{margin:'10px 0 28px'}}>Everything handled autonomously</h2>
        <div className="feature-cards">
          {[
            {icon:'🗺️', title:'Task Decomposition', desc:'Breaks one instruction into parallel agent tasks automatically.'},
            {icon:'🚆', title:'Transport Agent', desc:'Finds and ranks trains, buses, flights by price and preference.'},
            {icon:'🏨', title:'Hotel Agent', desc:'Selects hotels by rating, distance and budget fit.'},
            {icon:'⛅', title:'Weather Agent', desc:'Checks forecast and flags outdoor suitability per day.'},
            {icon:'🏛️', title:'Attraction Agent', desc:'Recommends attractions matched to your interests.'},
            {icon:'💰', title:'Budget Control', desc:'Calculates full breakdown and suggests cheaper alternatives.'},
          ].map(f=>(
            <div className="feature-card" key={f.title}>
              <span className="feature-icon">{f.icon}</span>
              <h4>{f.title}</h4>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="landing-cta">
        <img src="https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=900&q=80" alt="travel" className="landing-cta-img"/>
        <div className="landing-cta-text">
          <h2>Ready to plan your next trip?</h2>
          <p>One sentence is all it takes. AIVA handles the rest.</p>
          <Link className="button" to="/register">Start for free</Link>
        </div>
      </div>

      <div className="feature-strip" style={{padding:'30px 7vw 50px'}}>
        {['Task decomposition','Parallel agents','Dynamic replanning','Transparent logs','Voice input','Multilingual'].map(x=><span key={x}>{x}</span>)}
      </div>
    </div>
  )
}
