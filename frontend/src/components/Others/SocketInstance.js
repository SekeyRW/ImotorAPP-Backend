import io from 'socket.io-client';

// Define custom headers
const customHeaders = {
  'ngrok-skip-browser-warning': '69420'
};

// Create socket connection with custom headers
const socket = io(process.env.REACT_APP_SOCKET_URL, {
  extraHeaders: customHeaders
});

export { socket };