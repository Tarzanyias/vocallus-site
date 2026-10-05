// firebase-messaging-sw.js - shows Vocallus call alerts when the site isn't open.
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');
firebase.initializeApp({
  apiKey: "AIzaSyBqMft1lyqV3C1iD8V_X941fnQhHJXOOfU",
  authDomain: "vocallus-aa81e.firebaseapp.com",
  projectId: "vocallus-aa81e",
  storageBucket: "vocallus-aa81e.firebasestorage.app",
  messagingSenderId: "997486177218",
  appId: "1:997486177218:web:7c4741dbd450549140845b"
});
firebase.messaging();
