import {useEffect, useState} from "react";
import {useNavigate, useParams} from "react-router-dom";
import axios from "axios";
import {toast} from "react-toastify";
import Loading from "../../Others/Loading";
import ReactPaginate from "react-paginate";
import {Button, Modal} from "react-bootstrap";

function MakeModel() {
    const token = localStorage.getItem("token");
    const [pageNumber, setPageNumber] = useState(0);
    const [pageSize, setPageSize] = useState(10);
    const [total, setTotal] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setLoading] = useState(true)
    const [data, setData] = useState([])
    const [formData, setFormData] = useState({});
    const [showAddModal, setAddModal] = useState(false);
    const [showAddConfrimModal, setAddConfirmModal] = useState(false);
    const [isModifying, setModifying] = useState(false);

    const navigate = useNavigate();

    const {id} = useParams();
    const {brand_name} = useParams();
    const {brand_type} = useParams();

    const [update_id, setUpdateId] = useState('')
    const [showEditModal, setEditModal] = useState(false);
    const [showEditConfrimModal, setEditConfirmModal] = useState(false);

    const [deleteDataId, setDeleteDataId] = useState(null);
    const [deleteDataName, setDeleteDataName] = useState(null);
    const [showDeleteModal, setShowDeleteModal] = useState(false);

    const pageCount = Math.ceil(total / pageSize);
    const handlePageChange = ({selected}) => {
        setPageNumber(selected);
    };

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/admin/make-and-model-view/${id}?page=${pageNumber + 1}&page_size=${pageSize}&search=${searchTerm}`, {
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
    }, [id, pageNumber, pageSize, searchTerm, token])

    function confirmAddData(event) {
        event.preventDefault()
        setModifying(true)

        const formData = new FormData(event.target);

        const data = {
            name: formData.get("name"),
        };
        setFormData(data);
        setAddConfirmModal(true);
    }

    function handleAddData() {
        axios.post(`${process.env.REACT_APP_API_URL}/admin/make-and-model-create/${id}`, formData, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            }
        })
            .then(response => {
                if (response.status === 400) {
                    toast.error(response.data.message)
                } else {
                    const newData = response.data.new_data;
                    setData(prevData => [newData, ...prevData]);
                    toast.success(response.data.message)
                }
            })
            .catch(error => {
                console.log(error)
            })
            .finally(() => {
                setModifying(false)
                setAddModal(false)
            })
    }

    function confirmEditData(event) {
        event.preventDefault()
        setModifying(true)

        const formData = new FormData(event.target);

        const data = {
            name: formData.get("name"),
        };
        setFormData(data);
        setEditConfirmModal(true);
    }

    function handleEditData() {
        axios.put(`${process.env.REACT_APP_API_URL}/admin/make-and-model-update/${update_id}`, formData, {
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

    function confirmDeleteData(id, name) {
        setDeleteDataId(id);
        setDeleteDataName(`${name}`);
        setShowDeleteModal(true);
    }

    function handleDeleteData(id) {
        fetch(`${process.env.REACT_APP_API_URL}/admin/make-and-model-delete/${id}`, {
            method: 'DELETE', headers: {
                'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`,
            }
        })
            .then(response => {
                const updatedData = data.filter(item => item.id !== id);
                setData(updatedData);
                toast.success('Make & Model removed successfully.');
            })
            .catch(error => {
                console.error(error);
                toast.error('An error occurred while deleting data.');
            });
    }

    function handleTrim(id, name) {
        const make_name = encodeURIComponent(`${name}`);
        navigate(`/settings/make-and-model/trim/${id}/${make_name}`);
    }

    if (isLoading) {
        return (
            <Loading/>
        );
    }

    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Make & Model
                of {brand_name} ({brand_type.toUpperCase()})</h3>
            <div className="card shadow border-primary mb-3 mx-4">
                <div className="card-header">
                    <p className="text-primary m-0 fw-bold d-inline">Make & Model Information</p>
                    <button className="btn btn-primary text-end float-end btn-sm" onClick={() => {
                        setAddModal(true)
                    }}>Add New Make & Model
                    </button>
                </div>
                <div className="card-body rounded-3">
                    <div className="row g-3">
                        <div className='col-md-11'>
                            <input type="text" className="form-control" placeholder="Search Make & Model Name!"
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
                    </div>

                    <div className="table-responsive table mt-2" id="dataTable" role="grid"
                         aria-describedby="dataTable_info">
                        <table className="table my-0" id="dataTable">
                            <thead>
                            <tr>
                                <th>Name</th>
                                <th>Trim</th>
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
                                        <td>{data.name}</td>
                                        <td>
                                            <button className="btn btn-primary btn-sm mx-1"
                                                    onClick={() => handleTrim(data.id, data.name)}>
                                                Trim
                                            </button>
                                        </td>
                                        <td>
                                            <button className="btn btn-warning btn-sm mx-1" onClick={() => {
                                                setUpdateId(data.id)
                                                setFormData({
                                                    name: data.name,
                                                });
                                                setEditModal(true)
                                            }}><i className='fas fa-edit'></i></button>
                                            <button className="btn btn-danger btn-sm"
                                                    onClick={() => confirmDeleteData(data.id, data.name)}>
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

            <Modal
                size="lg"
                show={showAddModal}
                onHide={() => setAddModal(false)}
                aria-labelledby="example-modal-sizes-title-lg"
            >
                <Modal.Header closeButton>
                    <Modal.Title id="example-modal-sizes-title-lg">
                        Add New Make & Model
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <form onSubmit={confirmAddData}>
                        <label className="form-label">Make & Model Name</label>
                        <input className="form-control" type="text" name="name" id="name"
                               placeholder="Enter Make & Model Name"
                               required/>
                        <div className="align-content-end">
                            <button className="btn btn-primary float-end mt-3" disabled={isModifying}
                            >{isModifying ? <i className="fa fa-spinner fa-spin"></i> : "Add"}
                            </button>
                        </div>
                    </form>
                </Modal.Body>
            </Modal>

            <Modal show={showAddConfrimModal} onHide={() => setAddConfirmModal(false)} backdrop='static'>
                <Modal.Header>
                    <Modal.Title>Confirm Make & Model Details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p><strong>Make & Model Name:</strong> {formData.name}</p>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => {
                        setAddConfirmModal(false);
                        setModifying(false);
                    }
                    }>
                        Cancel
                    </Button>
                    <Button variant="primary" onClick={() => {
                        setAddConfirmModal(false);
                        handleAddData();
                    }}>
                        Confirm
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
                        Edit Make & Model Details
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <form onSubmit={confirmEditData}>
                        <label className="form-label">Make & Model Name</label>
                        <input className="form-control" type="text" name="name" id="name"
                               placeholder="Enter Make & Model Name"
                               value={formData.name}
                               onChange={(e) => setFormData({...formData, name: e.target.value})}
                               required/>
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
                    <Modal.Title>Confirm Make & Model Details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p><strong>Make & Model Name:</strong> {formData.name}</p>
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

            <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)} backdrop='static'>
                <Modal.Header>
                    <Modal.Title>Delete Make & Model</Modal.Title>
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
        </>
    )
}

export default MakeModel;