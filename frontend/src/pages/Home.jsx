import { useNavigate } from "react-router";

function Home() {
      const navigate = useNavigate();
    return (<><h1>Home</h1><br></br>
    <button    onClick={() => navigate('/login')} className="btn btn-primary">Login</button></>);
}
export default Home;