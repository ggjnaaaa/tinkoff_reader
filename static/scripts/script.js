//открыть форму для добавления записи
function openFormAdd() {
    const formAdd = document.querySelector('.add-form-container');
    formAdd.classList.add('open');
    const buttonClose = document.querySelector('.close-form-btn');
    //закрыть форму для добавления записи
    buttonClose.addEventListener('click', () => {
        formAdd.classList.remove('open');
    });
};
const formEdit = document.querySelector('#edit-form-container');

//открыть форму для редактирования записи
var btnsEditIncome = document.querySelectorAll('.tcol-filter-edit');

btnsEditIncome.forEach(function (btnEdit) {
    btnEdit.addEventListener('click', () => {
        let trEdit = btnEdit.parentNode.parentNode;
        trEdit.append(formEdit);
        const tdsEditForm = trEdit.children;
        console.log(tdsEditForm);
        setWidthEditForm(tdsEditForm);
        fillEditForm(tdsEditForm);
        formEdit.classList.add('open');
    });
});

function setWidthEditForm(data) {
    document.getElementById('edit-date').style.width = widthSub(data[1].offsetWidth);
    document.getElementById('edit-flight_id').style.width = widthSub(data[2].offsetWidth);
    document.getElementById('edit-type-of-route').style.width = widthSub(data[3].offsetWidth);
    document.getElementById('edit-technique_id').style.width = widthSub(data[4].offsetWidth);
    document.getElementById('edit-instructor').style.width = widthSub(data[5].offsetWidth);
    document.getElementById('edit-discount').style.width = widthSub(data[6].offsetWidth);
    document.getElementById('edit-checkbox-td').style.width = widthSub(data[7].offsetWidth);
    document.getElementById('edit-price').style.width = widthSub(data[8].offsetWidth);
    document.getElementById('edit-payment_type').style.width = widthSub(data[9].offsetWidth);
    document.getElementById('edit-source_id').style.width = widthSub(data[10].offsetWidth);
    document.getElementById('edit-note').style.width = widthSub(data[11].offsetWidth);
    document.getElementById('submit-edit').style.width = widthSub(data[12].offsetWidth);
};

function widthSub(str) {
    return (str - 4) + 'px';
};

//заполнить форму для редактирования записи
function fillEditForm(data) {
    document.getElementById('edit-id').value = data[0].innerHTML;
    console.log(data[1].innerHTML.slice(0, 10));
    document.getElementById('edit-date').value = data[1].innerHTML.slice(0, 10);
    document.getElementById('edit-flight_id').value = data[2].innerHTML;
    document.getElementById('edit-type-of-route').options[document.getElementById('edit-type-of-route').selectedIndex].text = data[3].innerHTML;
    document.getElementById('edit-technique_id').options[document.getElementById('edit-technique_id').selectedIndex].text = data[4].innerHTML;
    document.getElementById('edit-instructor').options[document.getElementById('edit-instructor').selectedIndex].text = data[5].innerHTML;
    document.getElementById('edit-discount').value = data[6].innerHTML;
    document.getElementById('edit-prepayment').checked = data[7].innerHTML === 'Да';
    document.getElementById('edit-price').value = data[8].innerHTML;
    document.getElementById('edit-payment_type').options[document.getElementById('edit-payment_type').selectedIndex].text = data[9].innerHTML;
    document.getElementById('edit-source_id').options[document.getElementById('edit-source_id').selectedIndex].text = data[10].innerHTML;
    document.getElementById('edit-note').value = data[11].innerHTML;
};

//заполнить форму для редактирования записи
//function fillEditForm(btnEdit, data) {
//    document.getElementById('edit-id').value = data.id;
//    document.getElementById('edit-date').innerHTML = data.date;
//    document.getElementById('edit-flight_id').value = data.flight_number;
//    document.getElementById('edit-type-of-route').options[document.getElementById('edit-type-of-route').selectedIndex].text = data.flight_name;
//    document.getElementById('edit-technique_id').options[document.getElementById('edit-technique_id').selectedIndex].text = data.technique_name;
//    document.getElementById('edit-instructor').options[document.getElementById('edit-instructor').selectedIndex].text = data.instructor;
//    document.getElementById('edit-discount').value = data.discount;
//    document.getElementById('edit-prepayment').checked = data.prepayment === 'Yes';
//    document.getElementById('edit-price').value = data.price;
//    document.getElementById('edit-payment_type').options[document.getElementById('edit-payment_type').selectedIndex].text = data.payment_type;
//    document.getElementById('edit-source_id').options[document.getElementById('edit-source_id').selectedIndex].text = data.source;
//    document.getElementById('edit-note').value = data.note;

//    let trEdit = btnEdit.parentNode.parentNode;
//    trEdit.append(formEdit);
//    const tdsEditForm = trEdit.children;
//    console.log(tdsEditForm);
//    setWidthEditForm(tdsEditForm);
//    formEdit.classList.add('open');
//};

//открыть форму для добавления пользователя в бот
function openFormAddBot() {
    const formAddBot = document.querySelector('#form-new-user-bot');
    formAddBot.classList.add('open');
    const buttonClose = document.querySelector('.close-form-btn');
    //закрыть форму для добавления записи
    buttonClose.addEventListener('click', () => {
        formAddBot.classList.remove('open');
    });
};

var tableBody = document.querySelector('#table-body');
const butttonAddOrder = document.querySelector('#submit');

//butttonAddOrder.addEventListener('click', (event) => {
//formAdd.classList.remove('open');
//event.preventDefault();
//document.querySelector('.add-entry-form').reset();
//});


const resizers = document.querySelectorAll('.resizer');

resizers.forEach(resizer => {
    resizer.addEventListener('mousedown', initDrag);

    function initDrag(e) {
        const th = e.target.parentElement;
        const startX = e.pageX;
        const startWidth = th.offsetWidth;

        function doDrag(e) {
            th.style.width = (startWidth + e.pageX - startX) + 'px';
        }

        function stopDrag() {
            window.removeEventListener('mousemove', doDrag);
            window.removeEventListener('mouseup', stopDrag);
            localStorage.setItem(th.innerText, th.style.width); // Сохраняем размер в локальное хранилище
        }

        window.addEventListener('mousemove', doDrag);
        window.addEventListener('mouseup', stopDrag);
    }
});

// Восстанавливаем размеры из локального хранилища
const headers = document.querySelectorAll('th');
headers.forEach(header => {
    const savedWidth = localStorage.getItem(header.innerText);
    if (savedWidth) {
        header.style.width = savedWidth;
    }
});

function toggleEdit(id) {
    const editFields = document.getElementById(`edit-fields-${id}`);
    if (editFields.style.display === 'none') {
        editFields.style.display = 'block';
    } else {
        editFields.style.display = 'none';
    }
};