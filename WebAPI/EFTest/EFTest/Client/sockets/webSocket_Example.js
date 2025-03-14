////////////////////////////////////////////////////////////
// This is example code on how the web app will connect to the Pi
/**https://chatgpt.com/share/67d463d0-8300-8011-a072-3115d87716f0 */
////////////////////////////////////////////////////////////

// Example client-side code for your web app
const connectToPi = (projectId) => {
    const ws = new WebSocket('ws://192.168.4.1:8765');
    
    ws.onopen = () => {
      console.log('Connected to Pi');
      
      // Sync project data
      syncProject(ws, projectId);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.command) {
        case 'sync_project_response':
          console.log('Project sync status:', data.message);
          break;
        case 'upload_file_response':
          console.log('File upload status:', data.message);
          break;
          
        case 'get_updates_response':
          processUpdatesFromPi(data.updates, projectId);
          break;
          
        case 'take_picture_response':
        case 'save_note_response':
          console.log(data.message);
          // Request updates to get the new files
          requestUpdates(ws, projectId);
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('Disconnected from Pi');
    };
    
    return ws;
  };
  
  const syncProject = (ws, projectId) => {
    // Get project data from your database
    fetchProjectData(projectId).then(projectData => {
      ws.send(JSON.stringify({
        command: 'sync_project',
        project_id: projectId,
        project_data: projectData
      }));
      
      // Upload project files
      uploadProjectFiles(ws, projectId);
    });
  };
  
  const uploadProjectFiles = (ws, projectId) => {
    // Get files from your database
    fetchProjectFiles(projectId).then(files => {
      files.forEach(file => {
        // Read file data and send it
        const reader = new FileReader();
        reader.onload = () => {
          const base64Data = reader.result.split(',')[1];
          
          ws.send(JSON.stringify({
            command: 'upload_file',
            project_id: projectId,
            file_name: file.name,
            file_type: file.type,
            file_data: base64Data
          }));
        };
        reader.readAsDataURL(file);
      });
    });
  };
  
  const requestUpdates = (ws, projectId) => {
    ws.send(JSON.stringify({
      command: 'get_updates',
      project_id: projectId
    }));
  };
  
  const processUpdatesFromPi = (updates, projectId) => {
    // Process and save updates to your database
    for (const [fileType, files] of Object.entries(updates)) {
      files.forEach(file => {
        // Convert base64 data to a file object
        const blob = base64ToBlob(file.file_data, getContentType(fileType));
        const fileObj = new File([blob], file.file_name);
        
        // Save to your database
        saveFileToDatabase(projectId, fileType, fileObj);
      });
    }
  };
  
  // Helper functions
  const base64ToBlob = (base64, contentType) => {
    const byteCharacters = atob(base64);
    const byteArrays = [];
    
    for (let i = 0; i < byteCharacters.length; i += 512) {
      const slice = byteCharacters.slice(i, i + 512);
      
      const byteNumbers = new Array(slice.length);
      for (let j = 0; j < slice.length; j++) {
        byteNumbers[j] = slice.charCodeAt(j);
      }
      
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }
    
    return new Blob(byteArrays, {type: contentType});
  };
  
  const getContentType = (fileType) => {
    switch(fileType) {
      case 'images': return 'image/jpeg';
      case 'notes': return 'text/plain';
      case 'documents': return 'application/pdf';
      default: return 'application/octet-stream';
    }
  };