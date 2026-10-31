import { useState } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
 
import Login from './pages/Login'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import 'bootstrap/dist/css/bootstrap.min.css';
import Home from './pages/Home'
import Chat from './pages/chat/Chat'
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/chat" element={<Chat />} />
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App
