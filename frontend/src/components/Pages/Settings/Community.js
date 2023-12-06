import {useEffect, useState} from "react";
import {useParams} from "react-router-dom";
import axios from "axios";
import {toast} from "react-toastify";
import Loading from "../../Others/Loading";
import ReactPaginate from "react-paginate";
import {Button, Modal} from "react-bootstrap";

function Community() {
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
    const [fileUrl, setFileUrl] = useState('');

    const {id} = useParams();
    const {location_name} = useParams();

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
        axios.get(`${process.env.REACT_APP_API_URL}/admin/community-view/${id}?page=${pageNumber + 1}&page_size=${pageSize}&search=${searchTerm}`, {
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
    }, [pageNumber, pageSize, searchTerm, token])

    function confirmAddData(event) {
        event.preventDefault();
        setModifying(true);

        const image = event.target.elements.image.files[0];
        const imageFileName = image ? image.name : ''; // Check if image is uploaded

        if (image) {
            // Check if the file extension is valid (PDF or image)
            const fileExtension = imageFileName.toLowerCase().split('.').pop();
            if (['jpg', 'jpeg', 'png'].includes(fileExtension)) {
                setFormData({
                    name: event.target.elements.name.value,
                    image: image,
                    image_name: imageFileName,
                });

                const fileUrl = URL.createObjectURL(image);
                setFileUrl(fileUrl);

                setAddConfirmModal(true);
            } else {
                // Display an error toast for invalid file type
                toast.error('Invalid file type. Only image files are allowed.');
                setModifying(false);
            }
        } else {
            // If no image is uploaded, proceed with just the name
            setFormData({
                name: event.target.elements.name.value,
            });

            setAddConfirmModal(true);
        }
    }

    function handleAddData() {
        axios.post(`${process.env.REACT_APP_API_URL}/admin/community-create/${id}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
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

        const imageFileInput = event.target.elements.image;

        if (imageFileInput && imageFileInput.files && imageFileInput.files.length > 0) {
            const image = imageFileInput.files[0];
            const imageFileName = image.name;

            const fileExtension = imageFileName.toLowerCase().split('.').pop();
            if (['pdf', 'jpg', 'jpeg', 'png'].includes(fileExtension)) {
                setFormData({
                    name: event.target.elements.name.value,
                    image: image,
                    image_name: imageFileName,
                });
                const fileUrl = URL.createObjectURL(image);
                setFileUrl(fileUrl);
                setEditConfirmModal(true);
            } else {
                // Display an error toast for invalid file type
                toast.error('Invalid file type. Only image files are allowed.');
                setModifying(false);
            }
        } else {
            setFormData({
                name: event.target.elements.name.value,
            });
            setEditConfirmModal(true);
        }


    }

    function handleEditData() {
        axios.put(`${process.env.REACT_APP_API_URL}/admin/community-update/${update_id}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data', 'Authorization': `Bearer ${token}`,
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
        fetch(`${process.env.REACT_APP_API_URL}/admin/community-delete/${id}`, {
            method: 'DELETE', headers: {
                'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`,
            }
        })
            .then(response => {
                const updatedData = data.filter(item => item.id !== id);
                setData(updatedData);
                toast.success('Community removed successfully.');
            })
            .catch(error => {
                console.error(error);
                toast.error('An error occurred while deleting data.');
            });
    }

    if (isLoading) {
        return (
            <Loading/>
        );
    }

    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Communities
                of {location_name}</h3>
            <div className="card shadow border-primary mb-3 mx-4">
                <div className="card-header">
                    <p className="text-primary m-0 fw-bold d-inline">Community Information</p>
                    <button className="btn btn-primary text-end float-end btn-sm" onClick={() => {
                        setAddModal(true)
                    }}>Add New Community
                    </button>
                </div>
                <div className="card-body rounded-3">
                    <div className="row g-3">
                        <div className='col-md-11'>
                            <input type="text" className="form-control" placeholder="Search Community Name!"
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
                                <th>Image</th>
                                <th>Name</th>
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
                                            <img src={`${process.env.REACT_APP_API_URL}/uploaded_img/${data.image}`}
                                                 className='rounded-1 img-fluid img-thumbnail'
                                                 alt="Thumbnail" style={{
                                                width: '50px',
                                                height: '50px',
                                            }}/>
                                        </td>
                                        <td>{data.name}</td>
                                        <td>
                                            <button className="btn btn-warning btn-sm mx-1" onClick={() => {
                                                setUpdateId(data.id)
                                                setFormData({
                                                    name: data.name,
                                                    image: data.image,
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
                        Add New Community
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <form onSubmit={confirmAddData} encType="multipart/form-data">
                        <label className="form-label">Community Name</label>
                        <input className="form-control" type="text" name="name" id="name"
                               placeholder="Enter Community Name"
                               required/>
                        <label className="form-label">Image</label>
                        <input className="form-control" type="file" name="image" id="image"/>
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
                    <Modal.Title>Confirm Location Details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p><strong>Community Name:</strong> {formData.name}</p>
                    <img src={fileUrl} alt="community_logo" style={{maxWidth: '100%', height: 'auto'}}/>
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
                        Edit Community Details
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <form onSubmit={confirmEditData} encType="multipart/form-data">
                        <label className="form-label">Community Name</label>
                        <input className="form-control" type="text" name="name" id="name"
                               placeholder="Enter Location Name"
                               value={formData.name}
                               onChange={(e) => setFormData({...formData, name: e.target.value})}
                               required/>
                        <label className="form-label">Image</label>
                        <input className="form-control" type="file" name="image" id="image"/>
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
                    <Modal.Title>Confirm Community Details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p><strong>Community Name:</strong> {formData.name}</p>
                    {fileUrl ? (
                        <>
                            <img src={fileUrl} alt="brand_logo" style={{maxWidth: '100%', height: 'auto'}}/>
                        </>
                    ) : null}

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
                    <Modal.Title>Delete Community</Modal.Title>
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

export default Community