// 全局保存选中ID的集合
const selectedIds = new Set();
function updateToggleSelectBtnStatus() {
  const totalCount = $('input[name="checkItem"]').length;
  const checkedCount = $('input[name="checkItem"]:checked').length;

  if (totalCount > 0 && checkedCount === totalCount) {
    $('#toggleSelectBtn').text('取消全选').data('status', 'selected');
  } else {
    $('#toggleSelectBtn').text('全选').data('status', 'unselected');
  }
}

layui.use(['laypage', 'form','jquery'], function() {
    var laypage = layui.laypage;
    var $ = layui.jquery;
    var form = layui.form;
    const token = localStorage.getItem('token');
    let  cid = 0;
    function resetCheckboxStatus() {
      $('#toggleSelectBtn').text('全选').data('status', 'unselected');
      $('input[type="checkbox"].row-checkbox').prop('checked', false);

      // 清除 selectedIds 中当前页所有的 id
      $('input[type="checkbox"].row-checkbox').each(function() {
        selectedIds.delete($(this).data('id'));
      });

      layui.use('form', function () {
        layui.form.render('checkbox');
      });
    }



    // 单选
    layui.use(['form'], function(){
      var form = layui.form;

      form.on('checkbox(checkItem)', function(data){
        const id = String($(data.elem).data('id'));
        console.log('checkbox changed, id:', id, 'checked:', data.elem.checked);

        if (data.elem.checked) {
          selectedIds.add(id);
        } else {
          selectedIds.delete(id);
        }

        console.log('selectedIds now:', Array.from(selectedIds));

        const totalCount = $('input[name="checkItem"]').length;
        const checkedCount = $('input[name="checkItem"]:checked').length;

        if (checkedCount === totalCount && totalCount > 0) {
          $('#toggleSelectBtn').text('取消全选').data('status', 'selected');
        } else {
          $('#toggleSelectBtn').text('全选').data('status', 'unselected');
        }
        updateToggleSelectBtnStatus()
      });
    });



    $('body').on('click', '#toggleSelectBtn', function() {
      const $btn = $(this);
      const isSelected = $btn.data('status') === 'selected';

      if (isSelected) {
        // 只删除当前页面的ID，而不是全部清空
        $('input[name="checkItem"]').each(function() {
          selectedIds.delete(String($(this).data('id')));
        });
        $('input[name="checkItem"]').prop('checked', false);
        $btn.text('全选').data('status', 'unselected');
      } else {
        // 全选，加入当前页面所有id
        $('input[name="checkItem"]').each(function() {
          selectedIds.add(String($(this).data('id')));
        });
        $('input[name="checkItem"]').prop('checked', true);
        $btn.text('取消全选').data('status', 'selected');
      }
    });

});