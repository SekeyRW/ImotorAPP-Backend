import React from 'react';
import {Link, useLocation, useNavigate} from 'react-router-dom';
import {toast} from "react-toastify";
import '../../assets/css/header.css'
import {NavDropdown} from "react-bootstrap";

function Header() {
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate("/");
        toast.success('Logged out Successfully')
    };

    const isActiveRoute = (route) => {
        return location.pathname === route;
    };

    return (
        <nav className="navbar navbar-dark align-items-start sidebar sidebar-dark accordion bg-gradient-primary p-0">
            <div className="container-fluid d-flex flex-column p-0"><Link
                className="navbar-brand d-flex justify-content-center align-items-center sidebar-brand m-0"
                to='/dashboard'
            >
                <div className="sidebar-brand-text mx-2"><span>Imotor App</span></div>
            </Link>
                <hr className="sidebar-divider my-0"/>
                <ul className="navbar-nav text-light" id="accordionSidebar">
                    <li className='nav-item'><Link to='/dashboard'
                                                   className={`nav-link${isActiveRoute('/dashboard') ? ' active' : ''}`}>
                        <i className="fas fa-tachometer-alt" aria-hidden="true"></i><span>Dashboard</span></Link></li>
                    <hr></hr>
                    <li className='nav-item'><Link to='/users-information'
                                                   className={`nav-link${isActiveRoute('/users-information') ? ' active' : ''}`}>
                        <i className="fas fa-users" aria-hidden="true"></i><span>Users</span></Link></li>
                    <hr></hr>
                    <NavDropdown
                        title={<><i className="fas fa-cogs" aria-hidden="true"></i><span>Settings</span></>}
                        menuVariant="dark"
                        drop='down-centered'
                    >
                        <>
                            <NavDropdown.Item>
                                <Link to='/settings/brands'
                                      className={`nav-link${isActiveRoute('/settings/brands') ? ' active' : ''}`}>
                                    <i className="fas fa-flag" aria-hidden="true"></i><span>Brands</span></Link>
                            </NavDropdown.Item>
                            <NavDropdown.Item>
                                <Link to='/settings/locations'
                                      className={`nav-link${isActiveRoute('/settings/locations') ? ' active' : ''}`}>
                                    <i className="fas fa-location-arrow"
                                       aria-hidden="true"></i><span>Locations</span></Link>
                            </NavDropdown.Item>
                        </>
                    </NavDropdown>
                    <hr></hr>
                    <br/>
                    <li className="nav-item"><Link className="nav-link" to='/' onClick={handleLogout}><i
                        className="fas fa-sign-out-alt"></i><span>Logout</span></Link>
                    </li>
                    <hr></hr>
                </ul>
            </div>
        </nav>
    );
}

export default Header;
