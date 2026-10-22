import axios from 'axios';
import { auth } from './firebaseConfig';

const API_URL = '/api';
// const API_URL = 'http://localhost:5001/api';

// Both numbering schemes are owned by the server: it generates the values and
// validates the stubs we send it, so the client just renders whatever it
// serves. Extending a scheme (a new department, a new series, a new branch of
// the drawing tree) is therefore a server-side change only.
//
// The whole scheme arrives in one response and every picker walks it in
// memory, so stepping through the drawing builder makes no further requests.
// The promise is memoised: the schemes change very rarely, so one request
// serves every component for the life of the page.
let schemesPromise = null;

export function loadNumberSchemes() {
  if (!schemesPromise) {
    // Start from a resolved promise so that a missing currentUser rejects the
    // returned promise rather than throwing synchronously at the call site.
    schemesPromise = Promise.resolve()
      .then(() => auth.currentUser.getIdToken(true))
      .then((idToken) =>
        axios.get(`${API_URL}/number_schemes`, {
          headers: { Authorization: `${idToken}` },
        })
      )
      .then((res) => ({
        drawingSteps: (res.data.drawing && res.data.drawing.steps) || [],
        documentStubs: (res.data.document && res.data.document.stubs) || [],
      }))
      .catch((error) => {
        // Don't cache a failure, so the next caller retries rather than being
        // stuck with an empty picker for the life of the page.
        schemesPromise = null;
        throw error;
      });
  }
  return schemesPromise;
}
