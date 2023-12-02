import {toast} from "react-toastify";
import {useEffect, useState} from "react";
import Loading from "../Others/Loading";
import {useNavigate} from "react-router-dom";
import axios from "axios";
import logo from '../../assets/image/logo.jpeg';

function Login() {
    const navigate = useNavigate();
    const token = localStorage.getItem('token');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setLoading] = useState(true)


    function handleLogin() {
        axios.post(`${process.env.REACT_APP_API_URL}/auth/admin/login`, {email, password}, {
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then((response) => {
                if (response.status === 200) {
                    localStorage.setItem('token', response.data.access_token);
                    toast.success('Logged in Successfully');
                    navigate('/dashboard');
                } else {
                    toast.error('Something went wrong. Please try again.');
                }
            })
            .catch((error) => {
                if (error.response && error.response.status === 401) {
                    toast.error(error.response.data.message);
                } else {
                    toast.error('Something went wrong. Please try again.');
                }
            });
    }

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/admin/initializer`)
            .then(response => {
            })
            .catch(error => {
                console.log(error)
            })
    }, [])

    useEffect(() => {
        const authenticated = Boolean(token);
        if (authenticated) {
            navigate('/dashboard');
        } else {
            setLoading(false)
        }
    }, [navigate, token]);

    if (isLoading) {
        return (
            <Loading/>
        );
    }

    return (
        <>
            <div className="row justify-content-center">
                <div className="col-md-9 col-lg-12 col-xl-10">
                    <div className="card shadow-lg o-hidden border-dark my-5 ">
                        <div className="card-body p-0">
                            <div className="row">
                                <div className="col-lg-6 d-none d-lg-flex">
                                    <div className="flex-grow-1 bg-login-image"
                                         style={{
                                             backgroundImage: `url(${logo.toString()})`,
                                             backgroundSize: 'cover',
                                             backgroundPosition: 'center',
                                             maxWidth: '100vh',
                                         }}></div>
                                </div>
                                <div className="col-lg-6">
                                    <div className="p-5">
                                        <div className="text-center">
                                            <h4 className="text-dark mb-4">Admin Login</h4>
                                        </div>
                                        <div className="mb-3">
                                            <input
                                                className='form-control'
                                                type="email"
                                                placeholder="Email"
                                                value={email}
                                                onChange={(e) => setEmail(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <div className="mb-3">
                                            <input
                                                className='form-control'
                                                type="password"
                                                placeholder="Password"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                required
                                            />
                                        </div>
                                        <button onClick={handleLogin}
                                                className='btn btn-primary d-block w-100'>Login
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="row">
                    <div className="col-12">
                        <footer className="footer">
                            <p className="text-center my-3">
                                &copy; {new Date().getFullYear()} Imotor App. All Rights Reserved.
                            </p>
                        </footer>
                    </div>
                </div>
            </div>
        </>
    )
}

export default Login
