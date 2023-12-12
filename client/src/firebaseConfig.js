import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth'

/* code from our Firebase console */
var firebaseConfig = {
    apiKey: "AIzaSyADo4ntri-lgH8vay94EjheNez_5HqoGgU",
    authDomain: "documents-index-ua.firebaseapp.com",
};

// Initialize Firebase
const firebaseApp = initializeApp(firebaseConfig);
const auth = getAuth(firebaseApp);

// generate & export auth object
export { auth };
