define(['jquery', 
    'underscore', 
    'knockout',
    'views/forms/wizard-base', 
    'views/forms/sections/branch-list',
    'views/forms/sections/validation',
    'bootstrap-datetimepicker',
    'arches',
    'dropzone',
    'summernote'], function ($, _, ko, WizardBase, BranchList, ValidationTools, datetimepicker, arches, dropzone, summernote) {
    var vt = new ValidationTools;
    return WizardBase.extend({
        initialize: function() {
            WizardBase.prototype.initialize.apply(this);

            var self = this;
            var dropzoneEl = this.$el.find('.dropzone');
            var date_picker = $('.datetimepicker').datetimepicker({pickTime: false});            
            this.getBlankFormData();
            date_picker.on('dp.change', function(evt){
                $(this).find('input').trigger('change'); 
            });
            self.startWorkflow();
            
            // detect if dropzone is attached, and if not init
            if (!dropzoneEl.hasClass('dz-clickable')) {
                this.dropzoneInstance = new dropzone(dropzoneEl[0], {
                    url: arches.urls.concept,
                    acceptedFiles: 'image/*',
                    addRemoveLinks: true,
                    autoProcessQueue: false
                });

                this.dropzoneInstance.on("addedfile", function(file) {
                    if (file.mock){

                    }else{
                        var el = self.el.appendChild(this.hiddenFileInput);
                        el.setAttribute('name', _.uniqueId('file_'));
                        self.filebranchlist.files.push({
                            file: file,
                            el: el
                        })
                        this.hiddenFileInput = false;
                    }
                });

                this.dropzoneInstance.on("removedfile", function(filetoremove) {
                    if (filetoremove.mock){
                        self.filebranchlist.deleteItem(filetoremove.branchlist);
                    }else{
                        var index;
                        _.each(self.filebranchlist.files, function(file, i){
                            if (file.file === filetoremove){
                                index = i;
                            }
                        }, this);

                        self.el.removeChild(self.filebranchlist.files[index].el);
                        self.filebranchlist.files.splice(index, 1);
                    }
                });
            }
    
            
            // step 1
            this.addBranchList(new BranchList({
                el: this.$el.find('#disturbances-section')[0],
                data: this.data,
                dataKey: 'DAMAGE_STATE.E3',
                validateBranch: function (nodes) {
                    var ck0 = vt.isValidDate(nodes,"DISTURBANCE_CAUSE_DATE_TO.E61");
                    var ck1 = vt.isValidDate(nodes,"DISTURBANCE_CAUSE_DATE_FROM.E61");
                    var ck2 = vt.isValidDate(nodes,"DISTURBANCE_CAUSE_DATE_OCCURRED_ON.E61");
                    var ck3 = vt.isValidDate(nodes,"DISTURBANCE_CAUSE_DATE_OCCURRED_BEFORE.E61");
                    return ck0 && ck1 && ck2 && ck3
                }
            }));
            
            // step 2
            this.filebranchlist = this.addBranchList(new BranchList({
                el: this.$el.find('#image-section')[0],
                data: this.data,
                dataKey: 'CONDITION_ASSESSMENT_IMAGE.E38',
                files: [],
                validateBranch: function (nodes) {
                    return true;
                },
                addMockFiles: function(){
                    self.dropzoneInstance.removeAllFiles();
                    $('.dz-preview.dz-image-preview').remove();
                    _.each(this.getBranchLists(), function(list){
                        // Create the mock file:
                        var mockFile = { name: '', size: 0, mock: true, branchlist: list};
                        var thumbnail = '';

                        // And optionally show the thumbnail of the file:
                        _.each(ko.toJS(list.nodes), function(node){
                            if (node.entitytypeid === 'CONDITION_ASSESSMENT_IMAGE.E38'){
                                mockFile.name = node.value
                            }
                            // if (node.entitytypeid === 'CONDITION_IMAGE_THUMBNAIL.E62'){
                                // thumbnail = node.value;
                            // }
                        }, this);

                        // Call the default addedfile event handler
                        self.dropzoneInstance.emit("addedfile", mockFile);
                        self.dropzoneInstance.emit("thumbnail", mockFile, thumbnail);

                        // Make sure that there is no progress bar, etc...
                        //self.dropzoneInstance.emit("complete", mockFile);

                        // If you use the maxFiles option, make sure you adjust it to the
                        // correct amount:
                        // var existingFileCount = 1; // The number of files already uploaded
                        // myDropzone.options.maxFiles = myDropzone.options.maxFiles - existingFileCount;
                    }, this);
                }
            }));
            
            // step 3
            this.addBranchList(new BranchList({
                el: this.$el.find('#threat-section')[0],
                data: this.data,
                dataKey: 'THREAT_INFERENCE_MAKING.I5',
                validateBranch: function (nodes) {
                    return this.validateHasValues(nodes);
                }
            }));
            
            // step 4
            this.addBranchList(new BranchList({
                el: this.$el.find('#recommendation-section')[0],
                data: this.data,
                dataKey: 'ACTIVITY_PLAN.E100',
                validateBranch: function (nodes) {
                    return this.validateHasValues(nodes);
                }
            }));
            
            this.listenTo(this,'change', this.dateEdit)
            
            this.events['click .disturbance-date-item'] = 'showDate';
            this.events['click .disturbance-date-edit'] = 'dateEdit';
        },
        
        
        dateEdit: function (e, b) {
            _.each(b.nodes(), function (node) {
                if (node.entitytypeid() == 'DISTURBANCE_DATE_FROM.E61' && node.value() && node.value() != '') {
                    $('.div-date').addClass('hidden')
                    $('.div-date-from-to').removeClass('hidden')
                    $('.disturbance-date-value').html('From-To')
                } else if (node.entitytypeid() == 'DISTURBANCE_DATE_OCCURRED_ON.E61' && node.value() && node.value() != '') {
                    $('.div-date').addClass('hidden')
                    $('.div-date-on').removeClass('hidden')
                    $('.disturbance-date-value').html('On')
                } else if (node.entitytypeid() == 'DISTURBANCE_DATE_OCCURRED_BEFORE.E61' && node.value() && node.value() != '') {
                    $('.div-date').addClass('hidden')
                    $('.div-date-before').removeClass('hidden')
                    $('.disturbance-date-value').html('Before')
                }
            })
        },
        
        
        showDate: function (e) {
            $('.div-date').addClass('hidden')
            $('.disturbance-date-value').html($(e.target).html())
            if ($(e.target).hasClass("disturbance-date-from-to")) {
                $('.div-date-from-to').removeClass('hidden')
            } else if ($(e.target).hasClass("disturbance-date-on")) {
                $('.div-date-on').removeClass('hidden')
            } else if ($(e.target).hasClass("disturbance-date-before")) {
                $('.div-date-before').removeClass('hidden')
            }
        },

        startWorkflow: function() {
            
            this.switchBranchForEdit(this.getBlankFormData());
        },

        switchBranchForEdit: function(branchData){
            this.prepareData(branchData);

            _.each(this.branchLists, function(branchlist){
                branchlist.data = branchData;
                branchlist.undoAllEdits();
            }, this);

            this.toggleEditor();
        },

        prepareData: function(assessmentNode){
            _.each(assessmentNode, function(value, key, list){
                assessmentNode[key].domains = this.data.domains;
            }, this);
            return assessmentNode;
        },

        getBlankFormData: function(){
            return this.prepareData({
                
                // step 1
                'DAMAGE_STATE.E3': {
                    'branch_lists':[]
                },
                
                // step 2
                'CONDITION_ASSESSMENT_IMAGE.E38': {
                    'branch_lists':[]
                },
                
                // step 3
                'THREAT_INFERENCE_MAKING.I5': {
                    'branch_lists':[]
                },
                
                // step 4
                'ACTIVITY_PLAN.E100': {
                    'branch_lists':[]
                },
            })
        },
        cancelWorkflow: function() { 
            this.cancel(); 
        },

    });
});