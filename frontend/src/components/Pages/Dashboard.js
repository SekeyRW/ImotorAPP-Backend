import axios from "axios";
import {toast} from "react-toastify";
import {useState} from "react";
import {Button, Modal} from "react-bootstrap";

function Dashboard() {
    const token = localStorage.getItem("token");
    const [showImportModal, setShowImportModal] = useState(false);

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

    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Dashboard</h3>
            <button className="btn btn-primary mx-5" onClick={() => {
                setShowImportModal(true)
            }}>Import Current User to Stripe
            </button>

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