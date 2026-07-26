import {createContext,useContext,useEffect,useMemo,useState} from 'react'
import {api} from '../api/client'
const AuthContext=createContext(null)
export function AuthProvider({children}){
 const [user,setUser]=useState(()=>JSON.parse(localStorage.getItem('user')||'null')); const [loading,setLoading]=useState(false)
 useEffect(()=>{if(localStorage.getItem('token')&&!user){api.get('/auth/me').then(r=>{setUser(r.data.data);localStorage.setItem('user',JSON.stringify(r.data.data))}).catch(()=>{})}},[])
 const login=async(email,password)=>{setLoading(true);try{const r=await api.post('/auth/login',{email,password});localStorage.setItem('token',r.data.data.access_token);localStorage.setItem('user',JSON.stringify(r.data.data.user));setUser(r.data.data.user);return r.data.data.user}finally{setLoading(false)}}
 const register=async(data)=>api.post('/auth/register',data)
 const logout=()=>{localStorage.removeItem('token');localStorage.removeItem('user');setUser(null)}
 return <AuthContext.Provider value={useMemo(()=>({user,loading,login,register,logout,setUser}),[user,loading])}>{children}</AuthContext.Provider>
}
export const useAuth=()=>useContext(AuthContext)
