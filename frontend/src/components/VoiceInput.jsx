import {useRef,useState} from 'react'
export default function VoiceInput({value,onChange,language='en-IN'}){
 const [listening,setListening]=useState(false); const recognition=useRef(null)
 const start=()=>{const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SpeechRecognition){alert('Speech recognition is not supported in this browser. Please type your request.');return} const r=new SpeechRecognition();r.lang=language;r.interimResults=true;r.onresult=e=>{let text='';for(let i=e.resultIndex;i<e.results.length;i++)text+=e.results[i][0].transcript;onChange(text)};r.onend=()=>setListening(false);r.onerror=()=>setListening(false);recognition.current=r;setListening(true);r.start()}
 const stop=()=>{recognition.current?.stop();setListening(false)}
 return <div className="voice-row"><button type="button" className={listening?'danger':''} onClick={listening?stop:start}>{listening?'Stop listening':'🎤 Speak request'}</button><span>{listening?'Listening…':'English, Tamil and Hindi supported'}</span></div>
}
