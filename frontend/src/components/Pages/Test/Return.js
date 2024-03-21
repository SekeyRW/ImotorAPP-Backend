import {useEffect, useState} from "react";
import axios from "axios";
import {Navigate} from "react-router-dom";

function Return() {
    const token = localStorage.getItem("token");
    const [status, setStatus] = useState(null);
    const [customerFullname, setCustomerFullname] = useState('');
    const [customerBillingEmail, setCustomerBillingEmail] = useState('');

    useEffect(() => {
        const queryString = window.location.search;
        const urlParams = new URLSearchParams(queryString);
        const sessionId = urlParams.get('session_id');

        axios.get(
            `${process.env.REACT_APP_API_URL}/session-status?session_id=${sessionId}`,
            {
                headers: {
                    'Authorization': `Bearer ${token}` // Set the Authorization header with the JWT token
                }
            }
        )
            .then((res) => {
                if (res.status === 200) {
                    setStatus(res.data.status);
                    setCustomerFullname(res.data.customer_fullname);
                    setCustomerBillingEmail(res.data.billing_email)
                } else {
                    throw new Error('Failed to fetch session status');
                }
            })
            .catch((error) => {
                console.error("Error fetching session status:", error);
            });
    }, [token]);

    if (status === 'open') {
        return (
            <Navigate to="/checkout"/>
        )
    }


    if (status === 'complete') {
        return (
            <section id="success">
                <p>
                    Hey {customerFullname}, We appreciate your business! A confirmation email will be sent to {customerBillingEmail} .

                    If you have any questions, please email <a href="mailto:info@imotor.app">info@imotor.app</a>.
                </p>
            </section>
        )
    }

    return null;

}

export default Return;