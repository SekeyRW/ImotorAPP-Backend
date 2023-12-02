import React, {useContext} from 'react';

function Footer() {
    return (
        <footer className="bg-white sticky-footer">
            <div className="container my-auto">
                <div className="text-center my-auto copyright"><span>Copyright&nbsp;© {new Date().getFullYear()} Imotor App </span>
                </div>
            </div>
        </footer>
    );
}

export default Footer;