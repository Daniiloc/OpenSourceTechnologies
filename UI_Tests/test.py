# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
#
# from main import app
#
#
# def first_test():
#     with app.test_request_context()
#     options = webdriver.ChromeOptions()
#     driver = webdriver.Chrome(options=options)
#     driver.get("")
#
#     # Поиск элементов и присваивание к переменным.
#     input_username = driver.find_element_by_xpath("//*[@id=\"user-name\"]")
#     input_password = driver.find_element_by_xpath("//*[@id=\"password\"]")
#     login_button = driver.find_element_by_xpath("//*[@id=\"login-button\"]")
#
#     # Действия с формами
#     input_username.send_keys("standard_user")
#     input_password.send_keys("secret_sauce")
#     login_button.send_keys(Keys.RETURN)
#
#     # Поиск и проверка попадания на главную страницу
#     title_text = driver.find_element_by_xpath("//*[@id=\"header_container\"]/div[2]/span")
#     if title_text.text == "PRODUCTS":
#         print("Мы попали на главную страницу")
#     else:
#         print("Ошибка поиска элемента")
#
#
#
# if __name__ == '__main__':
#     first_test()