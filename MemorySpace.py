#coding:utf-8
import cv2
import numpy

class Memory_Space(object):
    def __init__(self):
        #定义记忆空间
        self.MS=[]
        #定义储存数量
        self.num=50
        #定义已记忆的数量
        self.cnt=0


    def Update_Template(self,template,match_result,new_template):
        template_heigth, template_width = template.shape[:2]
        new_template_height, new_template_width = new_template.shape[:2]
        val = int(match_result * 10)
        if val >= 2:
            b = (val - 2) * 0.1
            img=cv2.resize(template,(new_template_width,new_template_height),cv2.INTER_CUBIC)
            img = img.astype(float) * (1 - b)
            new_template = new_template.astype(float) * b
            img = img.astype(numpy.uint8)
            new_template = new_template.astype(numpy.uint8)
            print ("----模板更新----")
            print("模板更新返回了两者之和")
            return img+new_template
        else:
            print("模板更新返回了原模板")
            return template


    def matchImg(self,last_img,current_img):
        if last_img.size !=0 and current_img.size !=0:
            last_img_heigth,last_img_width=last_img.shape[:2]
            current_img_heigth,current_img_width=current_img.shape[:2]

            #上一张图片面积比当前匹配的大
            if int(last_img_width*last_img_heigth)>int(current_img_width*current_img_heigth):
                img=cv2.resize(last_img,(current_img_width,current_img_heigth),cv2.INTER_CUBIC)
                result=cv2.matchTemplate(current_img,img,cv2.TM_CCOEFF_NORMED)
                _,max_val,_,_=cv2.minMaxLoc(result)
                val=float(max_val)
                print("匹配结果%.2f"%val)
                return val
            #上一张图片面积比当前匹配的小
            elif int(last_img_width*last_img_heigth)<int(current_img_width*current_img_heigth):
                img=cv2.resize(current_img,(last_img_width,last_img_heigth),cv2.INTER_CUBIC)
                result=cv2.matchTemplate(last_img,img,cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                val = float(max_val)
                print("匹配结果%.2f" % val)
                return val
            #上一张图片面积与当前匹配的一样大
            else:
                if last_img_width==current_img_width and last_img_heigth==current_img_heigth:
                    result=cv2.matchTemplate(last_img,current_img,cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)
                    val = float(max_val)
                    print("匹配结果%.2f" % val)
                    return val
                else:
                    img = cv2.resize(current_img, (last_img_width, last_img_heigth), cv2.INTER_CUBIC)
                    result = cv2.matchTemplate(last_img, img, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(result)
                    val = float(max_val)
                    print("匹配结果%.2f" % val)
                    return val
        else:
            print("******图片为空******")
            print("current_img.shape:", current_img.shape)
            print("template[0].shape:", last_img.shape)
            return 0.1


    def Recall(self,new_template,current_template,update_template=False):
        GET_SIMILAR_MERORY=False
        index=0
        global station
        for memory in self.MS:
            max_val=self.matchImg(current_template,new_template)
            index += 1
            print("记忆库中第%d模板匹配结果:%.2f"%(index,float(max_val)))
            if update_template==True:
                if max_val>0.3:
                    memory[1] += 1
                    memory[0] = self.Update_Template(memory[0], max_val, new_template)
                    station = memory
                    memory = current_template
                    print("----找到相似记忆:第%d个;记忆程度----" % index)
                    # print("----找到相似记忆:第%d个;记忆程度%d----" % (index, memory[1]))
                    GET_SIMILAR_MERORY=True
                    break
            elif update_template==False:
                if max_val>0.25:
                    memory[1]+=1
                    station = memory
                    print("----找到相似记忆:第%d个;记忆程度----" % index)
                    GET_SIMILAR_MERORY=True
                    break
        if update_template==True:
            if GET_SIMILAR_MERORY==True:
                return station,index-1
            elif GET_SIMILAR_MERORY==False:
                self.Remenber(new_template)
                return [new_template,1],len(self.MS)-1
        elif update_template==False:
            if GET_SIMILAR_MERORY==True:
                return station,index-1
            elif GET_SIMILAR_MERORY==False:
                return [current_template,1],0


    def Remenber(self,new_template):
        self.cnt+=1
        self.MS.append([new_template, 1])
        print ("----成功记忆第%d个模板,共有%d个模板----"%(self.cnt,len(self.MS)))
        cv2.imwrite(str(self.cnt)+".png",new_template)


    def Change(self,template,rank):
        self.MS[rank][0]=template


    def __Line_Up(self):
        pass