import axios from "axios";
import {toast} from "react-toastify";
import {useEffect, useState} from "react";
import {Button, Modal} from "react-bootstrap";
import Loading from "../Others/Loading";

function Dashboard() {
    const token = localStorage.getItem("token");
    const [showImportModal, setShowImportModal] = useState(false);
    const [isLoading, setLoading] = useState(true)
    const [subscribedUsersCount, setSubscribedUsersCount] = useState(0);
    const [publishedListingsCount, setPublishedListingsCount] = useState(0);
    const [inReviewListingsCount, setInReviewListingsCount] = useState(0);
     const [GCount, setGCount] = useState(0);

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/admin/dashboard`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(response => {
                setSubscribedUsersCount(response.data.subscribed_users_count);
                setPublishedListingsCount(response.data.published_listings_count);
                setInReviewListingsCount(response.data.in_review_listings_count);
                setGCount(response.data.google_installs);
            })
            .catch(error => {
                console.log(error)
            })
            .finally(() => {
                setLoading(false)
            })
    }, [token])

    function handleAddData() {
        axios.post(`${process.env.REACT_APP_API_URL}/import-all-user-to-stripe`, {
            headers: {
                'Authorization': `Bearer ${token}`,
            }
        })
            .then(response => {
                if (response.status === 400) {
                    toast.error(response.data.message)
                } else {
                    toast.success(response.data.message)
                }
            })
            .catch(error => {
                console.log(error)
            })
            .finally(() => {
                setShowImportModal(false)
            })
    }

    if (isLoading) {
        return (<Loading/>);
    }

    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Dashboard</h3>
            <div className='mb-3 mx-4'>
                <div className="row mb-3 mx-4">
                    <div className="col">
                        <div className="card shadow border-start-success py-2">
                            <div className="card-body">
                                <div className="row align-items-center no-gutters">
                                    <div className="col me-2">
                                        <div className="text-uppercase text-primary fw-semibold mb-2">
                                            <span>Subscribed to Package Users</span>
                                        </div>
                                        <div className="text-dark fw-bold h5 mb-0">
                                            <span>{subscribedUsersCount}</span>
                                        </div>
                                    </div>
                                    <div className="col-auto">
                                        <i className="fas fa-users fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="col">
                        <div className="card shadow border-start-success py-2">
                            <div className="card-body">
                                <div className="row align-items-center no-gutters">
                                    <div className="col me-2">
                                        <div className="text-uppercase text-primary fw-semibold mb-2">
                                            <span>Android Downloads</span>
                                        </div>
                                        <div className="text-dark fw-bold h5 mb-0">
                                            <span>{GCount}</span>
                                        </div>
                                    </div>
                                    <div className="col-auto">
                                        <i className="fas fa-users fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="row mb-3 mx-4">
                    <div className="col">
                        <div className="card shadow border-start-success py-2">
                            <div className="card-body">
                                <div className="row align-items-center no-gutters">
                                    <div className="col me-2">
                                        <div className="text-uppercase text-primary fw-semibold mb-2">
                                            <span>Published Listings</span>
                                        </div>
                                        <div className="text-dark fw-bold h5 mb-0">
                                            <span>{publishedListingsCount}</span>
                                        </div>
                                    </div>
                                    <div className="col-auto">
                                        <i className="fas fa-th-list fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="col">
                        <div className="card shadow border-start-success py-2">
                            <div className="card-body">
                                <div className="row align-items-center no-gutters">
                                    <div className="col me-2">
                                        <div className="text-uppercase text-primary fw-semibold mb-2">
                                            <span>In Review Listings</span>
                                        </div>
                                        <div className="text-dark fw-bold h5 mb-0">
                                            <span>{inReviewListingsCount}</span>
                                        </div>
                                    </div>
                                    <div className="col-auto">
                                        <i className="fas fa-th-list fa-2x text-gray-300"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <button className="btn btn-primary" onClick={() => {
                    setShowImportModal(true)
                }}>Import Current User to Stripe
                </button>
            </div>


            <Modal show={showImportModal} onHide={() => setShowImportModal(false)} backdrop='static'>
                <Modal.Header>
                    <Modal.Title>Import User to Stripe</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Are you sure you want Import all current user to stripe?</p>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowImportModal(false)}>
                        Cancel
                    </Button>
                    <Button variant="danger" onClick={() => {
                        handleAddData();
                        setShowImportModal(false);
                    }}>
                        Import
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    )
}

export default Dashboard