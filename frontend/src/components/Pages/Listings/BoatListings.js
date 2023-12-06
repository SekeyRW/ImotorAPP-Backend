import {useEffect, useState} from "react";
import axios from "axios";
import Loading from "../../Others/Loading";
import ReactPaginate from "react-paginate";

function BoatListings() {
    const token = localStorage.getItem("token");
    const [pageNumber, setPageNumber] = useState(0);
    const [pageSize, setPageSize] = useState(10);
    const [total, setTotal] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [data, setData] = useState([])
    const [isLoading, setLoading] = useState(true)

    const pageCount = Math.ceil(total / pageSize);
    const handlePageChange = ({selected}) => {
        setPageNumber(selected);
    };

    useEffect(() => {
        axios.get(`${process.env.REACT_APP_API_URL}/admin/boat-listing-view?page=${pageNumber + 1}&page_size=${pageSize}&search=${searchTerm}`, {
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

    if (isLoading) {
        return (
            <Loading/>
        );
    }
    return (
        <>
            <h3 className="text-white mb-3 mt-3 mx-4 bg-gradient-primary pt-4 pb-4 px-4 rounded-2">Boat
                Listings</h3>
            <div className="card shadow border-primary mb-3 mx-4">
                <div className="card-header">
                    <p className="text-primary m-0 fw-bold d-inline">Boat's Information</p>
                </div>
                <div className="card-body rounded-3">
                    <div className="row g-3">
                        <div className='col-md-11'>
                            <input type="text" className="form-control" placeholder="Search Boat Title!"
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
                                <th>Featured Image</th>
                                <th>Hin</th>
                                <th>Title</th>
                                <th>Price</th>
                                <th>Model</th>
                                <th>Model Year</th>
                                <th>Variant</th>
                                <th>Mileage</th>
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
        </>
    )
}

export default BoatListings;