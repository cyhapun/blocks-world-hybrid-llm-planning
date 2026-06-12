(define (problem bw_easy_008)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on_table b)
    (clear a)
    (clear b)
    (clear c)
    (handempty)
  )

  (:goal
    (on c a)
  )
)
