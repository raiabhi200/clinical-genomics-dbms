document.addEventListener("DOMContentLoaded", function () {
const forms = document.querySelectorAll("[data-confirm]");
forms.forEach(function (form) {
form.addEventListener("submit", function (event) {
const message = form.getAttribute("data-confirm");
if (!window.confirm(message)) {
event.preventDefault();
}
});
});
});
