export const StatusBadge=({status})=><span className={`badge ${String(status||'').toLowerCase()}`}>{status||'Unknown'}</span>
export const Spinner=()=> <div className="spinner">Planning your trip…</div>
export const Empty=({text='No data available'})=><div className="empty">{text}</div>
export const ErrorBox=({error})=>{
  if(!error) return null
  // No response reached the browser at all (backend down, CORS, DNS, etc.) —
  // axios surfaces this as a generic "Network Error" with no error.response.
  // Show something a non-technical user can act on instead.
  const friendly = !error.response
    ? 'Unable to connect to the AIVA backend. Please make sure the service is running and try again.'
    : (error?.response?.data?.error?.message || error?.response?.data?.detail || error.message || 'Something went wrong. Please try again.')
  return <div className="error-box">{friendly}</div>
}
export const ProgressBar=({value=0})=><div className="progress"><div style={{width:`${Math.min(100,value)}%`}}/><span>{Math.round(value)}%</span></div>
