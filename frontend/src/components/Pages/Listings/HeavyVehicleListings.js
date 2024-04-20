import {useEffect, useState} from "react";
import axios from "axios";
import Loading from "../../Others/Loading";
import ReactPaginate from "react-paginate";
import {toast} from "react-toastify";
import {Button, Modal} from "react-bootstrap";

function HeavyVehicleListings() {
    const token = localStorage.getItem("token");
    const [pageNumber, setPageNumber] = useState(0);
    const [pageSize, setPageSize] = useState(10);
    const [total, setTotal] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [data, setData] = useState([])
    const [isLoading, setLoading] = useState(true)

    const [deleteDataId, setDeleteDataId] = useState(null);
    const [deleteDataName, setDeleteDataName] = useState(null);
    const [showDeleteModal, setShowDeleteModal] = useState(false);

    const pageCount = Math.ceil(total / pageSize);
    const handlePageChange = ({selected}) => {
        setPageNumber(selected);
    };

    const [status, setStatus] = useState("ALL");
    const [update_id, setUpdateId] = useState('')
    const [showEditModal, setEditModal] = useState(false);
    const [showEditConfrimModal, setEditConfirmModal] = useState(false);
    const [isModifying, setModifying] = useState(false);
    const [formData, setFormData] = useState({});

    const publishStatusNames = {
        0: "IN REVIEW",
        1: "PUBLISHED",
        2: "NOT PUBLISHED",
    };

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/admin/heavy-vehicle-listing-view?page=${pageNumber + 1}&page_size=${pageSize}&search=${searchTerm}&status=${status}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
            .then(response => {
                setData(response.data.data)
                setTotal(response.data.total);
            })
            .catch(error => {
                console.log(error)
            })
            .finally(() => {
                setLoading(false)
            })
    }, [pageNumber, pageSize, searchTerm, token,status])

    function confirmDeleteData(id, name) {
        setDeleteDataId(id);
        setDeleteDataName(`${name}`);
        setShowDeleteModal(true);
    }

    function handleDeleteData(id) {
        fetch(`${process.env.REACT_APP_API_URL}/admin/delete-listing/${id}`, {
            method: 'DELETE', headers: {
                'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`,
            }
        })
            .then(response => {
                const updatedData = data.filter(item => item.id !== id);
                setData(updatedData);
                toast.success('Listing removed successfully.');
            })
            .catch(error => {
                console.error(error);
                toast.error('An error occurred while deleting data.');
            });
    }

    function confirmEditData(event) {
        event.preventDefault()
        setModifying(true)

        const formData = new FormData(event.target);

        const data = {
            publish_status: formData.get("publish_status"),
        };
        setFormData(data);
        setEditConfirmModal(true);
    }

    function handleEditData() {
        axios.put(`${process.env.REACT_APP_API_URL}/admin/update/listing-status/${update_id}`, formData, {
            headers: {
                'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`,
            }
        })
            .then(response => {
                if (response.status === 400) {
                    toast.error(response.data.message)
                } else {
                    const updatedData = response.data.updated_data;
                    const updatedIndex = data.findIndex(item => item.id === updatedData.id);
                    const updatedData2 = [...data];
                    updatedData2[updatedIndex] = updatedData;
                    setData(updatedData2);
                    toast.success(response.data.message)
                }
            })
            .catch(error => {
                if (error.response && error.response.status === 400) {
                    toast.error(error.response.data.message);
                } else {
                    console.log(error);
                    toast.error('Something went wrong. Please try again.');
                }
            })
            .finally(() => {
                setModifying(false)
                setEditModal(false)
                setUpdateId('')
            })
    }

    if (isLoading) {
        return (
            <Loading/>
        );
    }
    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Heavy Vehicle
                Listings</h3>
            <div className="card shadow border-primary mb-3 mx-4">
                <div className="card-header">
                    <p className="text-primary m-0 fw-bold d-inline">Heavy Vehicle's Information</p>
                </div>
                <div className="card-body rounded-3">
                    <div className="row g-3">
                        <div className='col-md-9'>
                            <input type="text" className="form-control" placeholder="Search Heavy Vehicle Title  or User Name!"
                                   aria-label="Search"
                                   aria-describedby="basic-addon2" value={searchTerm}
                                   onChange={e => setSearchTerm(e.target.value)}/>
                        </div>
                        <div className='col-md'>
                            <select className="form-control" value={pageSize} onChange={e => {
                                setPageSize(Number(e.target.value));
                                setPageNumber(0); // Reset the page number when the page size changes
                            }}>
                                <option value="10">10</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="40">40</option>
                                <option value="50">50</option>
                            </select>
                        </div>
                        <div className='col-md'>
                            <select className="form-control" value={status} onChange={e => {
                                setStatus(e.target.value);
                            }}>
                                <option value="ALL">ALL</option>
                                <option value="IN REVIEW">IN REVIEW</option>
                                <option value="NOT PUBLISHED">NOT PUBLISHED</option>
                                <option value="PUBLISHED">PUBLISHED</option>
                            </select>
                        </div>
                    </div>

                    <div className="table-responsive table mt-2" id="dataTable" role="grid"
                         aria-describedby="dataTable_info">
                        <table className="table my-0" id="dataTable">
                            <thead>
                            <tr>
                                <th>Featured Image</th>
                                <th>Vin</th>
                                <th>Title</th>
                                <th>Price</th>
                                <th>Model</th>
                                <th>Model Year</th>
                                <th>Variant</th>
                                <th>Mileage</th>
                                <th>User</th>
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
                                            <img
                                                src={`${process.env.REACT_APP_API_URL}/uploaded_img/${data.featured_image}`}
                                                className='rounded-1 img-fluid img-thumbnail'
                                                alt="Thumbnail" style={{
                                                width: '50px',
                                                height: '50px',
                                            }}/>
                                        </td>
                                        <td>{data.vin}</td>
                                        <td>{data.title}</td>
                                        <td>{data.price}</td>
                                        <td>{data.model}</td>
                                        <td>{data.model_year}</td>
                                        <td>{data.variant}</td>
                                        <td>{data.mileage}</td>
                                        <td>{data.user.first_name} {data.user.last_name}</td>
                                        <td>
                                            <button className="btn btn-warning btn-sm mx-1" onClick={() => {
                                                setUpdateId(data.id)
                                                setFormData({
                                                    publish_status: data.publish_status
                                                });
                                                setEditModal(true)
                                            }}><i className='fas fa-edit'></i></button>
                                            {data.publish_status === 0 && (
                                                <button className="btn btn-primary btn-sm mx-1"
                                                        onClick={() => window.open(`https://imotor.app/heavy-vehicle-details/${data.id}`)}>
                                                    Review
                                                </button>
                                            )}
                                            <button className="btn btn-danger btn-sm"
                                                    onClick={() => confirmDeleteData(data.id, data.title)}>
                                                <i
                                                    className='fas fa-trash-alt'></i></button>
                                        </td>

                                    </tr>
                                )))}
                            </tbody>
                        </table>
                    </div>
                    <ReactPaginate
                        pageCount={pageCount}
                        pageRangeDisplayed={5}
                        marginPagesDisplayed={2}
                        onPageChange={handlePageChange}
                        containerClassName="pagination justify-content-center mt-3"
                        activeClassName="active"
                        pageLinkClassName="page-link"
                        previousLinkClassName="page-link"
                        nextLinkClassName="page-link"
                        breakLinkClassName="page-link"
                        pageClassName="page-item"
                        previousClassName="page-item"
                        nextClassName="page-item"
                        breakClassName="page-item"
                        disabledClassName="disabled"
                    />
                </div>
            </div>

            <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} backdrop='static'>
                <Modal.Header>
                    <Modal.Title>Delete Listing</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Are you sure you want to delete {deleteDataName}?</p>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
                        Cancel
                    </Button>
                    <Button variant="danger" onClick={() => {
                        handleDeleteData(deleteDataId);
                        setShowDeleteModal(false);
                    }}>
                        Delete
                    </Button>
                </Modal.Footer>
            </Modal>

            <Modal
                size="lg"
                show={showEditModal}
                onHide={() => setEditModal(false)}
                aria-labelledby="example-modal-sizes-title-lg"
            >
                <Modal.Header closeButton>
                    <Modal.Title id="example-modal-sizes-title-lg">
                        Update Publish Status
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <form onSubmit={confirmEditData}>
                        <label className="form-label">Publish Status</label>
                        <select className="form-select" aria-label="Default select example" name="publish_status"
                                id="publish_status"
                                value={formData.publish_status}
                                onChange={(e) => setFormData({...formData, publish_status: e.target.value})}
                                required>
                            <option value="0">IN REVIEW</option>
                            <option value="1">PUBLISHED</option>
                            <option value="2">NOT PUBLISHED</option>
                        </select>
                        <div className="align-content-end">
                            <button className="btn btn-primary float-end mt-3" disabled={isModifying}
                            >{isModifying ? <i className="fa fa-spinner fa-spin"></i> : "Update"}
                            </button>
                        </div>
                    </form>
                </Modal.Body>
            </Modal>

            <Modal show={showEditConfrimModal} onHide={() => setEditConfirmModal(false)} backdrop='static'>
                <Modal.Header>
                    <Modal.Title>Confirm Publish Status</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p><strong>Publish Status:</strong> {publishStatusNames[formData.publish_status]}</p>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => {
                        setEditConfirmModal(false);
                        setModifying(false);
                    }}>
                        Cancel
                    </Button>
                    <Button variant="primary" onClick={() => {
                        setEditConfirmModal(false);
                        handleEditData();
                    }}>
                        Confirm
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    )
}

export default HeavyVehicleListings;