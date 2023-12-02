import Header from "./Header";
import Footer from "./Footer";
import '../../assets/css/mainlayout.min.css'
import {useNavigate} from "react-router-dom";
import {useEffect, useState} from "react";
import {toast} from "react-toastify";
import Loading from "../Others/Loading";

function Layout({element}) {
    const token = localStorage.getItem("token");
    const authenticated = Boolean(token);
    const exp = token ? JSON.parse(atob(token.split(".")[1])).exp : 0;
    const isExpired = exp && exp * 1000 < Date.now();
    const navigate = useNavigate();
    const [isLoading, setLoading] = useState(true)


    useEffect(() => {
        if (isExpired) {
            localStorage.removeItem("token");
            navigate("/");
            if (isExpired) {
                toast.error("Your session has expired. Please log in again.");
            }
        }
    }, [authenticated, isExpired, navigate]);

    useEffect(() => {
        if (!authenticated) {
            navigate("/");
            toast.error(
                "You cannot access this page."
            );
        } else {
            setLoading(false)
        }

    }, [authenticated, navigate]);

    if (isLoading) {
        return (
            <Loading/>
        );
    }


    return (
        <>
            <div id="wrapper">
                <Header/>
                <div className="d-flex flex-column" id="content-wrapper">
                    <div id="content">
                        {element}
                    </div>
                    <Footer/>
                </div>
            </div>
        </>

    )
}

export default Layout