 let currentAlerts = [];

        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    data.cameras.forEach(camera => {
                        const camElement = document.getElementById(`cam-${camera.id}`);
                        const statusIndicator = camElement.querySelector('.status-indicator');
                        const objectList = document.getElementById(`objects-${camera.id}`);
                        const fpsElement = document.getElementById(`fps-${camera.id}`);
                        window.aim_objects = [];
                        const hasPhone = camera.objects.some(obj =>
                            obj.toLowerCase().includes('cell phone'));
                        const hasBottle = camera.objects.some(obj =>
                            obj.toLowerCase().includes('bottle'));
                        const hasCup = camera.objects.some(obj =>
                            obj.toLowerCase().includes('cup'));

                        statusIndicator.className = `status-indicator ${camera.status === '运行中' ? 'online' : 'offline'}`;

                        if (hasPhone || hasBottle || hasCup) {
                        if(hasPhone){
                        camElement.classList.add('phone-alert');
                        aim_objects.push('手机、');
                        if (!currentAlerts.some(a => a.cameraId === camera.id)) {
                            currentAlerts.push({
                                cameraId: camera.id,
                                cameraName: camera.name,
                                timestamp: new Date().toLocaleTimeString(),
                                objects: camera.objects
                            });
                        }
                        }else{
                          // 删除aim_objects中的元素, 此处可不写, 因为下一帧后aim_objects将会重置.
//                        for (let i = 0; i < aim_objects.length; i++) {
//                          if (aim_objects[i] === '手机、') {
//                            aim_objects.splice(i, 1);
//                            i--;  // 调整索引以确保没有遗漏元素
//                          }
//                        }

                        }
                        if(hasBottle){
                        camElement.classList.add('phone-alert');
                        aim_objects.push('瓶子、');
                        if (!currentAlerts.some(a => a.cameraId === camera.id)) {
                            currentAlerts.push({
                                cameraId: camera.id,
                                cameraName: camera.name,
                                timestamp: new Date().toLocaleTimeString(),
                                objects: camera.objects
                            });
                        }
                        }else{
                             // 删除aim_objects中的元素, 此处可不写, 因为下一帧后aim_objects将会重置.
//                           for (let i = 0; i < aim_objects.length; i++) {
//                          if (aim_objects[i] === '瓶子、') {
//                            aim_objects.splice(i, 1);
//                            i--;  // 调整索引以确保没有遗漏元素
//                          }
//                        }

                        }
                        if(hasCup){
                        camElement.classList.add('phone-alert');
                        aim_objects.push('杯子、');
                        if (!currentAlerts.some(a => a.cameraId === camera.id)) {
                            currentAlerts.push({
                                cameraId: camera.id,
                                cameraName: camera.name,
                                timestamp: new Date().toLocaleTimeString(),
                                objects: camera.objects
                            });
                        }
                        }else{
                             // 删除aim_objects中的元素, 此处可不写, 因为下一帧后aim_objects将会重置.
//                           for (let i = 0; i < aim_objects.length; i++) {
//                          if (aim_objects[i] === '杯子、') {
//                            aim_objects.splice(i, 1);
//                            i--;  // 调整索引以确保没有遗漏元素
//                          }
//                        }

                        }


                        } else {
                            currentAlerts = currentAlerts.filter(a => a.cameraId !== camera.id);
                            camElement.classList.remove('phone-alert');
                            camElement.classList.remove('phone-alert');
                            camElement.classList.remove('phone-alert');
                        }

                        objectList.innerHTML = camera.objects.length > 0
                            ? camera.objects.map(obj => `<div class="object-tag">${obj}</div>`).join('')
                            : '<div class="object-tag">无检测目标</div>';

                        fpsElement.textContent = camera.fps || '-';
                    });

                    const onlineCount = data.cameras.filter(c => c.status === '运行中').length;
                    document.getElementById('online-count').textContent = onlineCount;

                    document.getElementById('cpu-usage').style.width = `${data.system.cpu}%`;
                    document.getElementById('mem-usage').style.width = `${data.system.memory}%`;

                    updateAlertSummary();
                });
        }

        function updateAlertSummary() {
            const alertCountElement = document.getElementById('alert-count');
            const alertStatusElement = document.getElementById('alert-status');
            const summaryCard = document.getElementById('alert-summary');

            if (currentAlerts.length > 0) {
                var aim_text = '检测到目标'.replace("目标",aim_objects);
                alertCountElement.textContent = currentAlerts.length;
                alertCountElement.className = 'alert-count has-alert';
                alertStatusElement.textContent = aim_text;
                alertStatusElement.style.color = 'var(--danger-color)';
                summaryCard.style.borderColor = 'rgba(255, 77, 77, 0.3)';
            } else {
                alertCountElement.textContent = '0';
                alertCountElement.className = 'alert-count no-alert';
                alertStatusElement.textContent = '系统正常';
                alertStatusElement.style.color = 'var(--success-color)';
                summaryCard.style.borderColor = 'rgba(255, 255, 255, 0.1)';
            }
        }

        async function showAlertDetails() {
            const modal = document.getElementById('alert-modal');
            const alertDetails = document.getElementById('alert-details');

            alertDetails.innerHTML = `
                <div class="alert-list-header">
                    <h3><i class="fas fa-exclamation-circle"></i> 当前活动警报</h3>
                </div>`;

            if (currentAlerts.length === 0) {
                alertDetails.innerHTML += `
                    <div class="no-alert">
                        <i class="fas fa-check-circle"></i>
                        <p>当前没有活动警报</p>
                    </div>`;
            } else {
                currentAlerts.forEach(alert => {
                    const alertItem = document.createElement('div');
                    alertItem.className = 'alert-item';
                    alertItem.innerHTML = `
                        <div class="alert-source">
                            <i class="fas fa-video"></i>
                            摄像头: ${alert.cameraName} (ID: ${alert.cameraId})
                        </div>
                        <div class="alert-time">
                            <i class="fas fa-clock"></i>
                            首次检测时间: ${alert.timestamp}
                        </div>
                        <div class="alert-objects">
                            <i class="fas fa-tag"></i>
                            检测目标: ${alert.objects.join(', ')}
                        </div>
                    `;
                    alertDetails.appendChild(alertItem);
                });
            }

            modal.style.display = 'block';
        }

        function closeModal() {
            document.getElementById('alert-modal').style.display = 'none';
        }

        function updateClock() {
            document.getElementById('live-clock').textContent =
                new Date().toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
        }

        document.getElementById('alert-summary').addEventListener('click', showAlertDetails);
        document.querySelector('.close-modal').addEventListener('click', closeModal);
        window.addEventListener('click', (event) => {
            if (event.target === document.getElementById('alert-modal')) {
                closeModal();
            }
        });

        setInterval(updateDashboard, 2000);
        setInterval(updateClock, 1000);
        updateDashboard();
        updateClock();