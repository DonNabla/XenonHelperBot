document.addEventListener('DOMContentLoaded', function() {
    const themeSwitcher = document.getElementById('themeSwitcher');
    const logoLight = document.querySelector('.logo-light');
    const logoDark = document.querySelector('.logo-dark');
    const navLinks = document.querySelectorAll('.navbar-nav li a');

    function toggleTheme(isDark) {
        if (logoLight && logoDark) {
            if (isDark) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
                logoLight.style.display = 'none';
                logoDark.style.display = 'block';
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                logoLight.style.display = 'block';
                logoDark.style.display = 'none';
            }
        }
    }

    function displayError(message) {
        // Placeholder function, can be expanded for custom notifications
        alert(message);
    }

    function setActiveNavLink() {
        navLinks.forEach(link => {
            if (window.location.pathname === new URL(link.href).pathname) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    function setupPagination(totalPages, currentPage) {
        const paginationControls = document.getElementById('paginationControls');
        paginationControls.innerHTML = '';

        for (let i = 1; i <= totalPages; i++) {
            const li = document.createElement('li');
            li.className = i === currentPage ? 'page-item active' : 'page-item';
            li.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            paginationControls.appendChild(li);
        }

        paginationControls.addEventListener('click', function(e) {
            e.preventDefault();
            if (e.target.tagName === 'A') {
                const selectedPage = parseInt(e.target.getAttribute('data-page'));
                fetchAndDisplayIssues(selectedPage);
            }
        });
    }

    const currentTheme = localStorage.getItem('theme');
    if (currentTheme) {
        themeSwitcher.checked = currentTheme === 'dark';
        toggleTheme(themeSwitcher.checked);
    }

    themeSwitcher.addEventListener('change', function() {
        toggleTheme(this.checked);
    });

    function fetchIssueCounts() {
        fetch('/get-issue-counts')
            .then(response => response.json())
            .then(data => {
                const primaryCard = document.querySelector('.card.bg-primary .card-title');
                const warningCard = document.querySelector('.card.bg-warning .card-title');
                const successCard = document.querySelector('.card.bg-success .card-title');

                if (primaryCard) primaryCard.textContent = data.total_issues;
                if (warningCard) warningCard.textContent = data.pending_issues;
                if (successCard) successCard.textContent = data.resolved_issues;
            })
            .catch(error => {
                console.error("Error fetching issue counts:", error);
                displayError("Error fetching issue counts. Please try again.");
            });
    }

    let currentPage = 1;
    const ITEMS_PER_PAGE = 5;

    function fetchAndDisplayIssues(page = 1) {
        fetch(`/get-issues?page=${page}&items_per_page=${ITEMS_PER_PAGE}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const table = document.getElementById('issuesTable');
                if (table) {
                    const tbody = table.getElementsByTagName('tbody')[0];
                    tbody.innerHTML = '';

                    data.issues.forEach(issue => {
                        let newRow = tbody.insertRow();

                        let cell1 = newRow.insertCell(0);
                        cell1.textContent = issue.submitted_at;

                        let cell2 = newRow.insertCell(1);
                        cell2.textContent = issue.user_id;

                        let cell3 = newRow.insertCell(2);
                        cell3.textContent = issue.issue_type;

                        let cell4 = newRow.insertCell(3);
                        cell4.textContent = issue.description;

                        let cell5 = newRow.insertCell(4);
                        cell5.textContent = issue.reproduce;

                        let cell6 = newRow.insertCell(5);
                        cell6.textContent = issue.log;

                        let cell7 = newRow.insertCell(6);
                        let badgeClass = issue.status === 'pending' ? 'badge-warning' : issue.status === 'resolved' ? 'badge-success' : 'badge-danger';
                        cell7.innerHTML = `<span class="badge ${badgeClass}">${issue.status}</span>`;
                    });

                    const totalPages = Math.ceil(data.total_issues / ITEMS_PER_PAGE);
                    setupPagination(totalPages, page);
                }
            })
            .catch(error => {
                console.error("Error fetching issues:", error);
                displayError("Error fetching issues. Please try again.");
            });
    }

    fetchAndDisplayIssues(currentPage);
    fetchIssueCounts();

    const refreshButton = document.getElementById('refreshButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', function(event) {
            event.stopPropagation();
            fetchAndDisplayIssues();
            fetchIssueCounts();
        });
    }

    const filterInput = document.getElementById('filterInput');
    if (filterInput) {
        filterInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('#issuesTable tbody tr');
            rows.forEach(row => {
                const description = row.cells[3].textContent.toLowerCase();
                if (description.includes(filterValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    setActiveNavLink();
});