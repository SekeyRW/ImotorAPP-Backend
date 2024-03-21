import {useEffect, useState} from "react";
import axios from "axios";
import Loading from "../../Others/Loading";
import {Button, Form, Modal} from "react-bootstrap";
import { jwtDecode } from "jwt-decode";

function Subscriptions() {
    const token = localStorage.getItem("token");
    const [data, setData] = useState([]);
    const [isLoading, setLoading] = useState(true)
    const [showModal, setShowModal] = useState(false);
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [selectedSubscriptionId, setSelectedSubscriptionId] = useState(null);
    const [selectedProductId, setSelectedProductId] = useState(null);
    const [newQuantity, setNewQuantity] = useState(1);
    const [unitPrice, setUnitPrice] = useState(0);
    const [profile, setProfile] = useState()

    // Decode the token
    const decodedToken = jwtDecode(token);

    // Extract user_id from the decoded token decodedToken.user_id;
    const userId = 28

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/get-user-subscription`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(response => {
                setData(response.data.data)
            })
            .catch(error => {
                console.log(error)
            })
            .finally(() => {
                setLoading(false)
            })
    }, [userId, token])

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/user-profile/${userId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(response => {
                setProfile(response.data.data)
            })
            .catch(error => {
                console.log(error)
            })
            .finally(() => {
                setLoading(false)
            })
    }, [userId,token])
    console.log(profile)

    const handleCancel = (subscriptionId) => {
        setSelectedSubscriptionId(subscriptionId);
        setShowCancelModal(true);
    };

    const handleUpgrade = (subscriptionId, unitPrice, quantity, productId) => {
        setSelectedSubscriptionId(subscriptionId);
        setSelectedProductId(productId);
        setUnitPrice(unitPrice);
        setNewQuantity(quantity);
        setShowModal(true);
    };

    const handleQuantityChange = (e) => {
        const quantity = parseInt(e.target.value);
        setNewQuantity(quantity);
    };

    const calculateTotalPrice = () => {
        return (unitPrice * newQuantity).toFixed(2);
    };

    const handleSubmitUpgrade = () => {
        // Call API to upgrade subscription with new quantity
        axios.put(
            `${process.env.REACT_APP_API_URL}/upgrade-subscription`,
            {
                subscriptionId: selectedSubscriptionId,
                productId: selectedProductId,
                newQuantity,
            },
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            }
        )
            .then((response) => {
                console.log('Subscription upgraded successfully:', response.data);
                // Fetch the updated subscription data from the server
                axios.get(`${process.env.REACT_APP_API_URL}/get-user-subscription`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                })
                    .then((response) => {
                        setData(response.data.data);
                    })
                    .catch((error) => {
                        console.error('Error fetching updated subscriptions:', error);
                    });
            })
            .catch((error) => {
                console.error('Error upgrading subscription:', error);
            })
            .finally(() => {
                setShowModal(false);
            });
    };

    const confirmCancel = () => {
        // Call API to cancel subscription
        axios.delete(`${process.env.REACT_APP_API_URL}/cancel-subscription/${selectedSubscriptionId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(response => {
                // Handle successful cancellation
                console.log(`Subscription with ID ${selectedSubscriptionId} cancelled successfully.`);
                // Reload subscription data
                axios.get(`${process.env.REACT_APP_API_URL}/get-user-subscription`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                })
                    .then(response => {
                        setData(response.data.data);
                    })
                    .catch(error => {
                        console.error('Error reloading subscription data:', error);
                    });
            })
            .catch(error => {
                console.error('Error cancelling subscription:', error);
            })
            .finally(() => {
                setShowCancelModal(false);
            });
    };

    if (isLoading) {
        return (
            <Loading/>
        );
    }


    return (
        <>
            <h2>User Subscriptions</h2>
            <div className="card shadow border-primary mb-3 mx-4">
                <div className="card-header">
                    <p className="text-primary m-0 fw-bold d-inline">Brand's Information</p>
                </div>
                <div className="card-body rounded-3">
                    <div className="row g-3">
                        Total Standard Listing: {profile.standard_listing}
                        Total Featured Listing: {profile.featured_listing}
                        Total Premium Listing: {profile.premium_listing}
                    </div>

                    <div className="table-responsive table mt-2" id="dataTable" role="grid"
                         aria-describedby="dataTable_info">
                        <table className="table my-0" id="dataTable">
                            <thead>
                            <tr>
                                <th>Packages</th>
                                <th>Price</th>
                                <th>Quantity</th>
                                <th>Total Price</th>
                                <th>Action</th>
                            </tr>
                            </thead>
                            <tbody className='table-group-divider'>
                            {data.length === 0 ? (
                                <tr>
                                    <td colSpan="9" className="text-center"><strong>No results found.</strong></td>
                                </tr>
                            ) : (
                                data.map((data) => (
                                    <tr key={data.id}>
                                        <td>
                                            {data.plan.product === "prod_PbPFZ2qSaqQFS5" && "PREMIUM PACKAGE"}
                                            {data.plan.product === "prod_PbPInhDd5zE2d5" && "ADDITIONAL PREMIUM LISTING"}
                                            {data.plan.product === "prod_PbPGcIZ8mGDgKt" && "ADDITIONAL STANDARD LISTING"}
                                            {data.plan.product === "prod_PbPEwLQCcVKadd" && "ADDITIONAL FEATURED LISTING"}
                                        </td>
                                        <td>{(data.plan.amount / 100).toFixed(2)}</td>
                                        <td>{data.quantity}</td>
                                        <td>{((data.plan.amount / 100) * data.quantity).toFixed(2)}</td>
                                        <td>
                                            <button className='btn' onClick={() => handleCancel(data.id)}>Cancel
                                            </button>
                                            {data.plan.product === "prod_PbPFZ2qSaqQFS5" ? null : (
                                                <button className='btn'
                                                        onClick={() => handleUpgrade(data.id, (data.plan.amount / 100), data.quantity, data.plan.product)}>Upgrade</button>
                                            )}
                                        </td>
                                    </tr>
                                )))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <Modal show={showModal} onHide={() => setShowModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Upgrade Subscription</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group controlId="quantity">
                            <Form.Label>Quantity</Form.Label>
                            <Form.Control
                                type="number"
                                value={newQuantity}
                                onChange={handleQuantityChange}
                            />
                        </Form.Group>
                        <Form.Group>
                            <Form.Label>Total Price</Form.Label>
                            <Form.Control plaintext readOnly value={`AED ${calculateTotalPrice()}`}/>
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
                    <Button variant="primary" onClick={handleSubmitUpgrade}>Upgrade</Button>
                </Modal.Footer>
            </Modal>

            <Modal show={showCancelModal} onHide={() => setShowCancelModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Cancel Subscription</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    Are you sure you want to cancel this subscription?
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowCancelModal(false)}>No</Button>
                    <Button variant="primary" onClick={confirmCancel}>Yes</Button>
                </Modal.Footer>
            </Modal>

        </>
    )
}

export default Subscriptions;