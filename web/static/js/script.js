//selecting all required elements

$(document).ready(function () {
	const dropArea1 = document.querySelector('.drag-area1'),
		dropArea2 = document.querySelector('.drag-area2'),
		btn1 = document.querySelector('#btn1'),
		btn2 = document.querySelector('#btn2'),
		input1 = document.querySelector('#input1'),
		input2 = document.querySelector('#input2'),
		btn3 = document.querySelector('#btn3');
	let file; //this is a global variable and we'll use it inside multiple functions

	var test = [];

	btn3.addEventListener('click', async function (e) {
		btn3.disabled = true;
		// console.log(test);
		var something = await Promise.all(
			test.map((f) => {
				return readFile(f);
			}),
		);
		var temp = JSON.stringify(something);
		// console.log(temp);
		fetch('/', {
			cache: 'no-cache',
			headers: {
				'Content-Type': 'application/json',
			},
			method: 'POST',
			body: temp,
		}).then(async (response) => {
			console.info('Sending Message ...');

			let data = await response.json();
			// console.log(data);
			const img = document.createElement('img');

			img.src = 'data:image/jpeg;base64,' + data;

			const res = document.querySelector('#result');

			btn3.innerText = 'Refresh';

			btn3.disabled = false;

			img.onload = function () {
				res.appendChild(img);
			};

			// console.info(response.json());
		});
	});

	btn1.onclick = () => {
		input1.click();
	};

	btn2.onclick = () => {
		input2.click();
	};

	input1.addEventListener('change', function () {
		file = this.files[0];
		dropArea1.classList.add('active');
		showFile(dropArea1, 'style');
	});

	input2.addEventListener('change', function () {
		file = this.files[0];
		dropArea2.classList.add('active');
		showFile(dropArea2, 'target');
	});

	//If user Drag File Over DropArea
	dropArea1.addEventListener('dragover', (event) => {
		event.preventDefault(); //preventing from default behaviour
		dropArea1.classList.add('active');
		// dragText.textContent = 'Release to Upload File';
	});

	//If user leave dragged File from DropArea
	dropArea1.addEventListener('dragleave', () => {
		dropArea1.classList.remove('active');
		// dragText.textContent = 'Drag & Drop to Upload File';
	});

	//If user drop File on DropArea
	dropArea1.addEventListener('drop', (event) => {
		event.preventDefault();
		console.log(event);
		file = event.dataTransfer.files[0];
		showFile(dropArea1, 'style'); //calling function
	});

	//If user Drag File Over DropArea
	dropArea2.addEventListener('dragover', (event) => {
		event.preventDefault(); //preventing from default behaviour
		dropArea2.classList.add('active');
		// dragText.textContent = 'Release to Upload File';
	});

	//If user leave dragged File from DropArea
	dropArea2.addEventListener('dragleave', () => {
		dropArea2.classList.remove('active');
		// dragText.textContent = 'Drag & Drop to Upload File';
	});

	//If user drop File on DropArea
	dropArea2.addEventListener('drop', (event) => {
		event.preventDefault();
		file = event.dataTransfer.files[0];
		showFile(dropArea2, 'target'); //calling function
	});

	function showFile(area, type) {
		let fileType = file.type; //getting selected file type
		if (fileType.match('image.*/')) {
			let fileReader = new FileReader();
			fileReader.onload = () => {
				let fileURL = fileReader.result;
				let imgTag = `<img src="${fileURL}" width="400px" height="400px" />`;
				area.innerHTML = imgTag;
				test.push({ [type]: fileURL });
			};
			fileReader.readAsDataURL(file);
		}
	}

	function readFile(file) {
		return new Promise((resolve, reject) => {
			return resolve(file);
		});
	}
});
