import ReactPaginate from "react-paginate";
import {useEffect, useState} from "react";
import axios from "axios";
import Loading from "../../Others/Loading";
import {Button, Modal} from "react-bootstrap";
import {toast} from "react-toastify";

function Brands() {
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

    const pageCount = Math.ceil(total / pageSize);
    const handlePageChange = ({selected}) => {
        setPageNumber(selected);
    };

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/admin/brand-view?page=${pageNumber + 1}&page_size=${pageSize}&search=${searchTerm}`, {
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
        event.preventDefault()
        setModifying(true)

        const image = event.target.elements.image.files[0];
        const imageFileName = image.name;

        // Check if the file extension is valid (PDF or image)
        const fileExtension = imageFileName.toLowerCase().split('.').pop();
        if (['pdf', 'jpg', 'jpeg', 'png'].includes(fileExtension)) {
            setFormData({
                name: event.target.elements.brand_name.value,
                type: event.target.elements.brand_type.value,
                image: image,
                image_name: imageFileName,
            });
            console.log(formData)
            const fileUrl = URL.createObjectURL(image);
            setFileUrl(fileUrl);

            setAddConfirmModal(true);
        } else {
            // Display an error toast for invalid file type
            toast.error('Invalid file type. Only image files are allowed.');
            setModifying(false);
        }
    }

    function handleAddData() {
        axios.post(`${process.env.REACT_APP_API_URL}/admin/brand-create`, formData, {
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

    if (isLoading) {
        return (
            <Loading/>
        );
    }

    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Brands</h3>
            <div className="card shadow border-primary mb-3 mx-4">
                <div className="card-header">
                    <p className="text-primary m-0 fw-bold d-inline">Brand's Information</p>
                    <button className="btn btn-primary text-end float-end btn-sm" onClick={() => {
                        setAddModal(true)
                    }}>Add New Brand
                    </button>
                </div>
                <div className="card-body rounded-3">
                    <div className="row g-3">
                        <div className='col-md-11'>
                            <input type="text" className="form-control" placeholder="Search Brand Name!"
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
                                <th>Type</th>
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
                                        <td>{data.type}</td>
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
                        Add New Brand
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <form onSubmit={confirmAddData} encType="multipart/form-data">
                        <label className="form-label">Brand Name</label>
                        <input className="form-control" type="text" name="brand_name" id="brand_name"
                               placeholder="Enter Brand Name"
                               required/>
                        <label className="form-label">Brand Type</label>
                        <select
                            className="form-select"
                            aria-label="Default select example"
                            name="brand_type"
                            id="brand_type"
                            required>
                            <option defaultValue>Select Brand Type</option>
                            <option value="car">Cars</option>
                            <option value="motorcycle">Motorcycle</option>
                            <option value="boat">Boats</option>
                            <option value="heavy vehicle">Heavy Vehicles</option>
                        </select>
                        <label className="form-label">Image</label>
                        <input className="form-control" type="file" name="image" id="image" required/>
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
                    <Modal.Title>Confirm Brand Details</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p><strong>Brand Name:</strong> {formData.name}</p>
                    <p><strong>Brand Type:</strong> {formData.type}</p>
                    <img src={fileUrl} alt="brand_logo" style={{maxWidth: '100%', height: 'auto'}}/>
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
        </>
    )
}

export default Brands
