import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth'

/* code from our Firebase console */
var firebaseConfig = {
    apiKey: 'AIzaSyBIoEnJQiULMZrrLgBxjDKH21FfYUMHHmg',
    authDomain: 'documents-index.firebaseapp.com',
};

// Initialize Firebase
const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);

// generate & export auth object
export { auth };
