import './App.css';
import {ToastContainer} from "react-toastify";
import {Route, Routes} from "react-router-dom";
import Login from "./components/Pages/Login";
import Layout from "./components/Layout/Layout";
import Dashboard from "./components/Pages/Dashboard";
import Brands from "./components/Pages/Settings/Brands";
import Locations from "./components/Pages/Settings/Locations";
import Community from "./components/Pages/Settings/Community";
import Users from "./components/Pages/Users";

function App() {
  return (
    <>
        <ToastContainer
                position="top-right"
                autoClose={3000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="colored"
            />
        <Routes>
            <Route path='/' element={<Login/>}/>
            <Route path='/dashboard' element={<Layout element={<Dashboard/>}/>}/>
             <Route path='/users-information' element={<Layout element={<Users/>}/>}/>
            <Route path='/settings/brands' element={<Layout element={<Brands/>}/>}/>
            <Route path='/settings/locations' element={<Layout element={<Locations/>}/>}/>
            <Route path='/settings/locations/communities/:id/:location_name' element={<Layout element={<Community/>}/>}/>
        </Routes>
    </>
  );
}

export default App;
