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
import CarListings from "./components/Pages/Listings/CarListings";
import MotorcycleListings from "./components/Pages/Listings/MotorcycleListings";
import BoatListings from "./components/Pages/Listings/BoatListings";
import HeavyVehicleListings from "./components/Pages/Listings/HeavyVehicleListings";
import MakeModel from "./components/Pages/Settings/MakeModel";
import Trim from "./components/Pages/Settings/Trim";
import Checkout from "./components/Pages/Test/Checkout";
import Return from "./components/Pages/Test/Return";
import Subscriptions from "./components/Pages/Test/Subscriptions";

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
                <Route path='/listings/cars' element={<Layout element={<CarListings/>}/>}/>
                <Route path='/listings/motorcycle' element={<Layout element={<MotorcycleListings/>}/>}/>
                <Route path='/listings/boats' element={<Layout element={<BoatListings/>}/>}/>
                <Route path='/listings/heavy-vehicles' element={<Layout element={<HeavyVehicleListings/>}/>}/>
                <Route path='/settings/brands' element={<Layout element={<Brands/>}/>}/>
                <Route path='/settings/brands/make-and-model/:id/:brand_name/:brand_type' element={<Layout element={<MakeModel/>}/>}/>
                <Route path='/settings/make-and-model/trim/:id/:make_name' element={<Layout element={<Trim/>}/>}/>
                <Route path='/settings/locations' element={<Layout element={<Locations/>}/>}/>
                <Route path='/settings/locations/communities/:id/:location_name'
                       element={<Layout element={<Community/>}/>}/>
                 <Route path="/checkout" element={<Checkout/>} />
                <Route path="/return" element={<Return/>} />
                <Route path="/subscriptions" element={<Subscriptions/>} />
            </Routes>
        </>
    );
}

export default App;
