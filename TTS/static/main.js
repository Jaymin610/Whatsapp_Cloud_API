// $(document).ready(function () {

//     $("#addBtn").on("click", function (){
//         window.location.replace("/admin/adduser")
//     });
    
//     $('#toggle-btn').on("click", function () {
//         console.log("Yes");
//         $(this).text($(this).text() == 'Hide Search' ? 'Show Search' : 'Hide Search');
//         $('#myBtn').toggle();
//         $('#clrBtn').toggle();
//         $('.hidden-table').switchClass('hidden-table', 'temp');
//         $('.temp').switchClass('temp', 'hidden-table');
        
//         console.log("Reach");
//     });

//     $('#myBtn').on("click", function () {
//         var fdate = $('#fromdate').val();
//         var tdate = $('#todate').val();
//         var cname = $('#cname').val();
//         var mname = $('#mname').val();
//         var stat = $('#stat').val();
//         var json = { name: "Ajax", age: "25", fdate: fdate, tdate: tdate, cname: cname, mname: mname, stat: stat }
//         $.ajax({
//             type: 'POST',
//             url: "/customers",
//             data: JSON.stringify(json),
//             contentType: "application/json; charset=utf-8",
//             dataType: 'json',
//             success: function (result) {
//                 console.log(result);
//                 $('#tbody-exam').remove()
//                 $('#example').append('<tbody id="tbody-exam"> }</tbody>');
//                 jQuery.each(result, function (k, v) {
//                     $('#tbody-exam').append('<tr><td><input type="checkbox" name="' + v.companyName + '" id=""></td><td> ' + v.companyName + '</td><td>' + v.name + '</td><td>' + v.Status + '</td><td>' + v.RegDate + '</td><td>' + v.validitydate + '</td><td> <a class="btn btn-primary" href="/show/camera/' + v.mobileNumber + '" role="button">ShowDevice</a></td>/tr>');
//                 });
//             },

//         });
//     });

//     $('#clrBtn').on("click", function () {
//         // $('#fdate').val('');
//         // $('#tdate').val('');
//         // $('#cname').val('');
//         // $('#mname').val('');
//         // $('#stat').val('');
//         location.reload(true);
//     });

//     $('#dltBtn').on('click', function () {
//         if (confirm("Your devices and data will be removed Permenantly. \n You want to go ahead ?") == true){
//             var selected = [];
//             $('#example tbody tr').each(function () {
//                 var t = $(this).children("td").children("input");
//                 if (t.is(":checked")) {
//                     selected.push(t.attr('name'));
//                 }
//             });
//             var json = { name: "delete", data: selected }
//             $.ajax({
//                 type: 'POST',
//                 url: "/deleteData",
//                 data: JSON.stringify(json),
//                 contentType: "application/json; charset=utf-8",
//                 dataType: 'json',
//                 success: function (result) {
//                     $('#tbody-exam').remove()
//                     $('#example').append('<tbody id="tbody-exam"> }</tbody>');
//                     jQuery.each(result, function (k, v) {
//                         $('#tbody-exam').append('<tr><td><input type="checkbox" name="' + v.companyName + '" id=""></td><td> ' + v.companyName + '</td><td>' + v.name + '</td><td>' + v.Status + '</td><td>' + v.RegDate + '</td><td>' + v.validitydate + '</td><td> <a class="btn btn-primary" href="/show/camera/' + v.mobileNumber + '" role="button">ShowDevice</a></td>/tr>');
//                     });
//                 },
//             })
//         }
//     });

//     $('#dltAllBtn').on('click', function () {
//         if (confirm("Whole database will be cleared Permenantly. \n You want to go ahead ?") == true) {
//             var json = { name: "deleteAll" }
//             $.ajax({
//                 type: 'POST',
//                 url: "/deleteData",
//                 data: JSON.stringify(json),
//                 contentType: "application/json; charset=utf-8",
//                 dataType: 'json',
//                 success: function (result) {
//                     location.reload(true);
//                 },
//             })
//         }
//     });

//     $('#expAllBtn').on('click', function(){
//         window.open("http://192.168.29.136:5000/export")
//     });

//     $('#expBtn').on('click', function () {
//         var selected = [];
//         $('#example tbody tr').each(function () {
//             var t = $(this).children("td").children("input");
//             if (t.is(":checked")) {
//                 selected.push(t.attr('name'));
//             }
//         });
//         var json = { name: "delete", data: selected }
//         $.ajax({
//             type: 'POST',
//             url: "/export",
//             data: JSON.stringify(json),
//             contentType: "application/json; charset=utf-8",
//             dataType: 'json',
//             success: function (result) {
//                 console.log(result);
//             },
//         })
//         window.open("http://192.168.29.136:5000/exportRow")
//     });

// })    