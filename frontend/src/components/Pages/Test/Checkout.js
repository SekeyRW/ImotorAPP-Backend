import {loadStripe} from "@stripe/stripe-js";
import {useEffect, useState} from "react";
import axios from "axios";
import {EmbeddedCheckout, EmbeddedCheckoutProvider} from "@stripe/react-stripe-js";
import { jwtDecode } from "jwt-decode";

function Checkout() {
    const token = localStorage.getItem("token");
    const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_KEY)
    const [clientSecret, setClientSecret] = useState('');

    useEffect(() => {
        axios.post(
            `${process.env.REACT_APP_API_URL}/create-checkout-session`,
            {}, // Pass empty data since you're not sending any request body
            {
                headers: {
                    'Authorization': `Bearer ${token}` // Set the Authorization header with the JWT token
                }
            }
        )
            .then((res) => setClientSecret(res.data.clientSecret))
            .catch((error) => console.error("Error fetching client secret:", error));
    }, [token]);

    return (
        <>
            <div id="checkout">
                <br/>
                <br/>
                {clientSecret && (
                    <EmbeddedCheckoutProvider
                        stripe={stripePromise}
                        options={{clientSecret}}
                    >
                        <EmbeddedCheckout/>
                    </EmbeddedCheckoutProvider>
                )}
            </div>
        </>
    )
}

export default Checkout;