document.addEventListener("DOMContentLoaded", function () {

    function sendMail(event) {
        event.preventDefault();

        var form = document.getElementById('form');
        var from_name = document.getElementsByName("f-name")[0].value;
        var email_id = document.getElementsByName("email")[0].value;
        var rating = document.getElementsByName("Rate Our Services")[0].value;
        var feedback = document.getElementsByName("Feedback")[0].value;
        var improve = document.getElementsByName("improvement")[0].value;
        var recommend = document.getElementsByName("recommend")[0].value;
        var addition = document.getElementsByName("addition")[0].value;

        if (!from_name || !email_id || !feedback || !rating || !improve || !recommend || !addition) {
            document.getElementById('message').innerHTML = "Please fill out all fields!!";
            document.getElementById('message').style.color = "red";
            return;
        }

        var params = {
            from_name: from_name,
            email_id: email_id,
            rating: rating,
            feedback: feedback,
            improve: improve,
            recommend: recommend,
            addition: addition
        };

        const serviceID = "service_e1a36ma";
        const templateID = "template_uh7nfyl";

        emailjs.send(serviceID, templateID, params)
            .then(res => {
                document.getElementsByName("f-name")[0].value = "";
                document.getElementsByName("email")[0].value = "";
                document.getElementsByName("Rate Our Services")[0].value = "";
                document.getElementsByName("Feedback")[0].value = "";
                document.getElementsByName("improvement")[0].value = "";
                document.getElementsByName("recommend")[0].value = "";
                document.getElementsByName("addition")[0].value = "";
                form.reset();
                console.log(res);
                document.getElementById('message').innerHTML = "Your feedback sent successfully!!";
                document.getElementById('message').style.color = "green";
            })
            .catch(err => console.error("Error sending email:", err));
    }

    document.getElementById('form').addEventListener("submit", sendMail);

});
