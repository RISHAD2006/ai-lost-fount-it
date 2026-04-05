const API = window.location.origin;

/* LOGOUT */

function logout(){
    localStorage.clear();
    window.location = "/login-page";
}

/* SOCKET CONNECTION */

const socket = io(API);

socket.on("connect", () => {
    console.log("Socket connected");
});

/* AI MATCH EVENT */

socket.on("match_found", data => {

    const user_id = localStorage.getItem("user_id");

    if(data.user1 == user_id || data.user2 == user_id){

        const popup = document.getElementById("popup");

        if(popup){
            popup.style.display = "block";

            setTimeout(()=>{
                popup.style.display = "none";
            },4000);
        }

        loadItems();
    }

});

/* UPLOAD ITEM */

async function uploadItem(){

    const user_id = localStorage.getItem("user_id");

    const title = document.getElementById("title").value;
    const description = document.getElementById("description").value;
    const status = document.getElementById("status").value;
    const image = document.getElementById("image").files[0];

    if(!title || !description || !image){
        alert("Please fill all fields");
        return;
    }

    const form = new FormData();

    form.append("title",title);
    form.append("description",description);
    form.append("status",status);
    form.append("user_id",user_id);
    form.append("image",image);

    try{

        const res = await fetch(API + "/upload",{
            method:"POST",
            body:form
        });

        if(!res.ok){
            throw new Error("Upload failed");
        }

        const data = await res.json();

        alert(data.message || "Upload success");

        document.getElementById("title").value="";
        document.getElementById("description").value="";
        document.getElementById("image").value="";

        loadItems();

    }catch(err){

        console.error(err);
        alert("Upload failed");

    }

}

/* LOAD ITEMS */

async function loadItems(){

    const user_id = localStorage.getItem("user_id");

    if(!user_id) return;

    try{

        const res = await fetch(API + "/my-items/" + user_id);

        if(!res.ok){
            throw new Error("Failed to load items");
        }

        const items = await res.json();

        const container = document.getElementById("items");

        if(!container) return;

        container.innerHTML="";

        items.forEach(i=>{

            container.innerHTML += `
            <div class="item">

            <img src="${i.image_url}" alt="item">

            <h4>${i.title}</h4>

            <p>${i.description}</p>

            <span class="badge ${i.status}">
            ${i.status}
            </span>

            ${i.matched ? '<span class="badge match">AI MATCH</span>' : ''}

            <br><br>

            <button onclick="deleteItem(${i.id})">
            Delete
            </button>

            </div>
            `;
        });

    }catch(err){

        console.log(err);

    }

}

/* DELETE ITEM */

async function deleteItem(id){

    if(!confirm("Delete item?")) return;

    try{

        const res = await fetch(API + "/delete/" + id,{
            method:"DELETE"
        });

        if(res.ok){
            loadItems();
        }

    }catch(err){

        console.log(err);

    }

}

/* INITIAL LOAD */

loadItems();
